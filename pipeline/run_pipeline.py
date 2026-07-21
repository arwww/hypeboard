from __future__ import annotations

import argparse
import json
import logging
import math
import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from dateutil import parser as date_parser

from pipeline.logging_config import configure_logging
from pipeline.models import (
    DataStatus,
    HistoryPoint,
    LatestPayload,
    LatestSymbol,
    MetaPayload,
    SourceRunStatus,
    SymbolConfig,
    SymbolHistoryPayload,
    UpdateReport,
)
from pipeline.scoring.confidence_score import calculate_confidence
from pipeline.scoring.hype_score import calculate_score_bundle
from pipeline.scoring.normalization import add_rolling_robust_features, percentile_rank
from pipeline.sources.base import AdapterResult, SourceAdapter
from pipeline.sources.finra_short_volume import FinraShortVolumeAdapter
from pipeline.sources.market_data import MarketDataAdapter
from pipeline.sources.social import SocialAttentionAdapter
from pipeline.sources.wikipedia import WikipediaPageviewsAdapter
from pipeline.validation.data_quality import validate_payloads
from pipeline.validation.export_schemas import export_schemas

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
LEGAL_NOTICE = (
    "Hypeboard stellt keine Anlageberatung und keine Kauf- oder Verkaufsempfehlung dar. "
    "Die dargestellten Werte basieren auf öffentlichen Marktdaten und Näherungsindikatoren. "
    "Der Hype Score misst keine exakten Brokerpositionen und keinen exakten Anteil von Privatanlegern."
)



def _write_json(path: Path, model: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2), encoding="utf-8")



def fetch_source_safely(
    adapter: SourceAdapter,
    universe: list[SymbolConfig],
    as_of: datetime,
    *,
    offline: bool,
) -> AdapterResult:
    """Keep an unexpected adapter defect from taking down all other sources."""
    try:
        return adapter.fetch(universe, as_of, offline=offline)
    except Exception as exc:  # final isolation boundary around provider code
        LOGGER.exception(
            "source adapter failed outside its normal error boundary",
            extra={"source": adapter.source_name, "error": str(exc)},
        )
        empty = pd.DataFrame()
        return AdapterResult(
            data=empty,
            status=adapter.status(
                status=DataStatus.UNAVAILABLE,
                retrieved_at=as_of,
                data=empty,
                error=f"unexpected adapter failure: {exc}",
            ),
        )

def load_configuration() -> tuple[list[SymbolConfig], dict[str, Any]]:
    universe_payload = json.loads(
        (ROOT / "pipeline" / "config" / "universe.json").read_text(encoding="utf-8")
    )
    universe = [SymbolConfig.model_validate(item) for item in universe_payload if item["active"]]
    score_config = json.loads(
        (ROOT / "pipeline" / "config" / "score_config.json").read_text(encoding="utf-8")
    )
    return universe, score_config


def prepare_market(frame: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.date
    result = result.sort_values(["symbol", "date"])
    computed_return = result.groupby("symbol")["close"].pct_change(fill_method=None) * 100
    if "daily_return_pct" in result.columns:
        result["daily_return_pct"] = pd.to_numeric(
            result["daily_return_pct"], errors="coerce"
        ).fillna(computed_return)
    else:
        result["daily_return_pct"] = computed_return
    result["dollar_volume"] = result["close"] * result["volume"]
    result["intraday_range_pct"] = (
        (result["high"] - result["low"]) / result["close"].replace(0, np.nan) * 100
    )
    min_obs = config["minimum_history_observations"]
    window = config["history_window_days"]
    clip = config["robust_z_clip"]
    result = add_rolling_robust_features(
        result,
        group_column="symbol",
        date_column="date",
        value_column="volume",
        prefix="volume",
        window=window,
        min_observations=min_obs,
        clip=clip,
    )
    result["volume_ratio_30d"] = result["volume"] / result["volume_median"].replace(0, np.nan)
    result["rolling_volatility_10d"] = (
        result.groupby("symbol")["daily_return_pct"]
        .transform(lambda series: series.rolling(10, min_periods=5).std())
    )
    result = add_rolling_robust_features(
        result,
        group_column="symbol",
        date_column="date",
        value_column="rolling_volatility_10d",
        prefix="volatility",
        window=window,
        min_observations=min_obs,
        clip=clip,
    )
    return result


def prepare_wikipedia(frame: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.date
    result = add_rolling_robust_features(
        result,
        group_column="symbol",
        date_column="date",
        value_column="pageviews",
        prefix="wikipedia",
        window=config["history_window_days"],
        min_observations=config["minimum_history_observations"],
        clip=config["robust_z_clip"],
    )
    result["wikipedia_change_pct"] = (
        (result["pageviews"] / result["wikipedia_median"].replace(0, np.nan)) - 1
    ) * 100
    return result


def prepare_finra(frame: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.date
    result = add_rolling_robust_features(
        result,
        group_column="symbol",
        date_column="date",
        value_column="short_volume_ratio",
        prefix="finra_short_ratio",
        window=20,
        min_observations=min(5, config["minimum_history_observations"]),
        clip=config["robust_z_clip"],
    )
    return result


def prepare_social(frame: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.date
    return add_rolling_robust_features(
        result,
        group_column="symbol",
        date_column="date",
        value_column="mentions",
        prefix="social",
        window=config["history_window_days"],
        min_observations=config["minimum_history_observations"],
        clip=config["robust_z_clip"],
    )


def _latest_by_symbol(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["symbol"])
    ordered = frame.sort_values(["symbol", "date"])
    latest = ordered.groupby("symbol", as_index=False).tail(1).copy()
    latest[f"{prefix}_date"] = latest["date"]
    drop = ["date"]
    return latest.drop(columns=drop)


def combine_latest(
    universe: list[SymbolConfig],
    market: pd.DataFrame,
    wikipedia: pd.DataFrame,
    finra: pd.DataFrame,
    social: pd.DataFrame,
) -> pd.DataFrame:
    base = pd.DataFrame([item.model_dump() for item in universe])
    latest = base.merge(_latest_by_symbol(market, "market"), on="symbol", how="left")
    latest = latest.merge(
        _latest_by_symbol(wikipedia, "wikipedia"), on="symbol", how="left", suffixes=("", "_wiki")
    )
    latest = latest.merge(
        _latest_by_symbol(finra, "finra"), on="symbol", how="left", suffixes=("", "_finra")
    )
    latest = latest.merge(
        _latest_by_symbol(social, "social"), on="symbol", how="left", suffixes=("", "_social")
    )
    return latest


def add_cross_sectional_signals(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["wikipedia_attention_score"] = percentile_rank(result.get("wikipedia_robust_z", pd.Series(index=result.index, dtype=float)))
    result["social_attention_score"] = percentile_rank(result.get("social_robust_z", pd.Series(index=result.index, dtype=float)))
    result["unusual_volume_score"] = percentile_rank(result.get("volume_robust_z", pd.Series(index=result.index, dtype=float)))
    abs_return = pd.to_numeric(result.get("daily_return_pct"), errors="coerce").abs()
    result["absolute_move_score"] = percentile_rank(abs_return)
    result["volatility_shock_score"] = percentile_rank(result.get("volatility_robust_z", pd.Series(index=result.index, dtype=float)))
    result["short_sale_change_score"] = percentile_rank(result.get("finra_short_ratio_robust_z", pd.Series(index=result.index, dtype=float)))
    result["additional_retail_proxy_score"] = result["social_attention_score"]
    result["short_term_activity_score"] = result[
        ["unusual_volume_score", "absolute_move_score"]
    ].mean(axis=1, skipna=True)
    result.loc[
        result[["unusual_volume_score", "absolute_move_score"]].isna().all(axis=1),
        "short_term_activity_score",
    ] = np.nan

    dollar_volume = pd.to_numeric(result.get("dollar_volume"), errors="coerce")
    result["price_impact_raw"] = abs_return / np.log1p(dollar_volume.replace(0, np.nan))
    result["price_impact_score"] = percentile_rank(result["price_impact_raw"])
    result["liquidity_sensitivity_score"] = percentile_rank(
        dollar_volume, higher_is_stronger=False
    )
    result["attention_shock_size_score"] = result["wikipedia_attention_score"]
    return result


def _history_counts(symbol: str, frames: dict[str, pd.DataFrame]) -> dict[str, int]:
    return {
        name: int(frame.loc[frame["symbol"] == symbol, "date"].nunique())
        if not frame.empty and "symbol" in frame
        else 0
        for name, frame in frames.items()
    }


def _to_date(value: Any) -> date | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return pd.to_datetime(value).date()


def _to_optional_float(value: Any, digits: int = 2) -> float | None:
    if value is None or pd.isna(value) or math.isinf(float(value)):
        return None
    return round(float(value), digits)


def _to_optional_int(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(round(float(value)))


def generate_drivers(row: pd.Series, component_coverage: dict[str, float], status: DataStatus) -> list[str]:
    drivers: list[str] = []
    volume_z = row.get("volume_robust_z")
    if volume_z is not None and not pd.isna(volume_z) and abs(float(volume_z)) >= 1.5:
        direction = "über" if float(volume_z) > 0 else "unter"
        drivers.append(
            f"Das Handelsvolumen liegt {abs(float(volume_z)):.1f} robuste Standardabweichungen {direction} dem 30-Tage-Niveau."
        )
    wiki_change = row.get("wikipedia_change_pct")
    if wiki_change is not None and not pd.isna(wiki_change) and abs(float(wiki_change)) >= 25:
        verb = "gestiegen" if float(wiki_change) > 0 else "gesunken"
        drivers.append(
            f"Wikipedia-Aufrufe sind gegenüber dem vorherigen 30-Tage-Median um {abs(float(wiki_change)):.0f} % {verb}."
        )
    short_z = row.get("finra_short_ratio_robust_z")
    if short_z is not None and not pd.isna(short_z) and float(short_z) >= 1.5:
        drivers.append("Das von FINRA gemeldete Short-Sale-Volumen ist relativ zur eigenen jüngeren Historie ungewöhnlich hoch.")
    daily_return = row.get("daily_return_pct")
    if daily_return is not None and not pd.isna(daily_return) and abs(float(daily_return)) >= 5:
        drivers.append(f"Die Aktie bewegte sich am letzten Handelstag um {float(daily_return):+.1f} %.")
    incomplete = [name for name, coverage in component_coverage.items() if coverage < 0.5]
    if incomplete:
        labels = {
            "attention": "Attention",
            "trading": "Trading Activity",
            "retail_proxy": "Retail Proxy",
            "impact": "Market Impact",
        }
        drivers.append(
            "Begrenzte Datenabdeckung bei " + ", ".join(labels[name] for name in incomplete) + "."
        )
    if status in {DataStatus.CACHED, DataStatus.STALE}:
        drivers.append("Mindestens eine verwendete Quelle stammt aus dem letzten erfolgreichen Cache oder ist veraltet.")
    return drivers[:5] or ["Für diese Beobachtung wurde kein einzelner Treiber oberhalb der konfigurierten Erklärschwelle identifiziert."]


def determine_status(row: pd.Series, hype_score: float | None, confidence: float, as_of: date) -> DataStatus:
    if hype_score is None:
        return DataStatus.UNAVAILABLE
    source_statuses = [
        row.get("source_status"),
        row.get("source_status_wiki"),
        row.get("source_status_finra"),
        row.get("source_status_social"),
    ]
    if DataStatus.CACHED.value in source_statuses:
        return DataStatus.CACHED
    dates = [_to_date(row.get(name)) for name in ["market_date", "wikipedia_date", "finra_date"]]
    if any(item and (as_of - item).days > 7 for item in dates):
        return DataStatus.STALE
    if confidence < 65 or any(item is None for item in dates):
        return DataStatus.PARTIAL
    return DataStatus.FRESH


def score_latest(
    frame: pd.DataFrame,
    *,
    source_frames: dict[str, pd.DataFrame],
    score_config: dict[str, Any],
    as_of: datetime,
) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    enriched = add_cross_sectional_signals(frame)
    confidence_parts: dict[str, dict[str, float]] = {}
    rows: list[dict[str, Any]] = []
    for _, row in enriched.iterrows():
        bundle = calculate_score_bundle(row, score_config)
        confidence, parts = calculate_confidence(
            row=row,
            as_of=as_of.date(),
            history_counts=_history_counts(row["symbol"], source_frames),
            config=score_config,
        )
        status = determine_status(row, bundle["hype_score"], confidence, as_of.date())
        payload = row.to_dict()
        payload.update(bundle)
        payload["confidence_score"] = confidence
        payload["data_status"] = status.value
        payload["drivers"] = generate_drivers(row, bundle["component_coverage"], status)
        rows.append(payload)
        confidence_parts[row["symbol"]] = parts
    scored = pd.DataFrame(rows)
    ranked = scored["hype_score"].rank(method="min", ascending=False, na_option="bottom")
    scored["rank"] = ranked.where(scored["hype_score"].notna()).astype("Int64")
    return scored, confidence_parts


def build_daily_panel(
    universe: list[SymbolConfig],
    market: pd.DataFrame,
    wikipedia: pd.DataFrame,
    finra: pd.DataFrame,
    social: pd.DataFrame,
    score_config: dict[str, Any],
) -> pd.DataFrame:
    dates: set[date] = set()
    for frame in [market, wikipedia, finra, social]:
        if not frame.empty:
            dates.update(frame["date"].dropna().tolist())
    if not dates:
        return pd.DataFrame()
    base = pd.MultiIndex.from_product(
        [[item.symbol for item in universe], sorted(dates)], names=["symbol", "date"]
    ).to_frame(index=False)
    columns_market = [
        "symbol", "date", "close", "daily_return_pct", "volume", "volume_ratio_30d",
        "volume_robust_z", "volatility_robust_z", "dollar_volume",
    ]
    columns_wiki = [
        "symbol", "date", "pageviews", "wikipedia_change_pct", "wikipedia_robust_z",
    ]
    columns_finra = [
        "symbol", "date", "short_volume_ratio", "finra_short_ratio_robust_z",
    ]
    columns_social = ["symbol", "date", "mentions", "social_robust_z"]
    panel = base
    for frame, columns in [
        (market, columns_market),
        (wikipedia, columns_wiki),
        (finra, columns_finra),
        (social, columns_social),
    ]:
        available = [column for column in columns if column in frame.columns]
        if not frame.empty and len(available) > 2:
            panel = panel.merge(frame[available], on=["symbol", "date"], how="left")
    scored_days: list[pd.DataFrame] = []
    for _, day in panel.groupby("date", sort=True):
        enriched = add_cross_sectional_signals(day)
        bundles = [calculate_score_bundle(row, score_config) for _, row in enriched.iterrows()]
        for key in ["attention_score", "trading_score", "retail_proxy_score", "impact_score", "hype_score", "score_coverage"]:
            enriched[key] = [bundle[key] for bundle in bundles]
        scored_days.append(enriched)
    if not scored_days:
        return panel
    all_columns = list(dict.fromkeys(column for day in scored_days for column in day.columns))
    trimmed_days = [day.dropna(axis=1, how="all") for day in scored_days]
    return pd.concat(trimmed_days, ignore_index=True, sort=False).reindex(columns=all_columns)


def previous_snapshot(
    panel: pd.DataFrame, latest_date: date | None
) -> tuple[dict[str, int], dict[str, float]]:
    if panel.empty or latest_date is None:
        return {}, {}
    candidates = sorted(item for item in panel["date"].unique() if item < latest_date)
    for candidate in reversed(candidates):
        day = panel[(panel["date"] == candidate) & panel["hype_score"].notna()].copy()
        if day.empty:
            continue
        day["rank"] = day["hype_score"].rank(method="min", ascending=False).astype(int)
        ranks = dict(zip(day["symbol"], day["rank"], strict=False))
        scores = dict(zip(day["symbol"], day["hype_score"].astype(float), strict=False))
        return ranks, scores
    return {}, {}


def create_outputs(
    universe: list[SymbolConfig],
    score_config: dict[str, Any],
    source_results: dict[str, Any],
    as_of: datetime,
) -> tuple[LatestPayload, MetaPayload, list[SymbolHistoryPayload], UpdateReport]:
    market = prepare_market(source_results["market"].data, score_config)
    wikipedia = prepare_wikipedia(source_results["wikipedia"].data, score_config)
    finra = prepare_finra(source_results["finra"].data, score_config)
    social = prepare_social(source_results["social"].data, score_config)
    source_frames = {"market": market, "wikipedia": wikipedia, "finra": finra, "social": social}

    latest_frame = combine_latest(universe, market, wikipedia, finra, social)
    scored_latest, confidence_parts = score_latest(
        latest_frame, source_frames=source_frames, score_config=score_config, as_of=as_of
    )
    panel = build_daily_panel(universe, market, wikipedia, finra, social, score_config)
    market_date = max(market["date"]) if not market.empty else None
    source_latest_dates = [
        max(frame["date"])
        for frame in [market, wikipedia, finra, social]
        if not frame.empty and "date" in frame
    ]
    latest_signal_date = max(source_latest_dates) if source_latest_dates else as_of.date()
    old_ranks, old_scores = previous_snapshot(panel, latest_signal_date)

    latest_symbols: list[LatestSymbol] = []
    for _, row in scored_latest.sort_values(["rank", "symbol"], na_position="last").iterrows():
        rank = _to_optional_int(row.get("rank"))
        previous = old_ranks.get(row["symbol"])
        rank_change = previous - rank if rank is not None and previous is not None else None
        current_hype = _to_optional_float(row.get("hype_score"), 1)
        previous_hype = old_scores.get(row["symbol"])
        hype_score_change = (
            round(current_hype - previous_hype, 1)
            if current_hype is not None and previous_hype is not None
            else None
        )
        latest_symbols.append(
            LatestSymbol(
                symbol=row["symbol"],
                company_name=row["company_name"],
                exchange=row["exchange"],
                sector=row["sector"],
                price=_to_optional_float(row.get("close"), 3),
                daily_return_pct=_to_optional_float(row.get("daily_return_pct"), 2),
                volume=_to_optional_int(row.get("volume")),
                volume_ratio_30d=_to_optional_float(row.get("volume_ratio_30d"), 2),
                attention_score=_to_optional_float(row.get("attention_score"), 1),
                trading_score=_to_optional_float(row.get("trading_score"), 1),
                retail_proxy_score=_to_optional_float(row.get("retail_proxy_score"), 1),
                impact_score=_to_optional_float(row.get("impact_score"), 1),
                hype_score=current_hype,
                hype_score_change=hype_score_change,
                confidence_score=float(row["confidence_score"]),
                rank=rank,
                rank_change=rank_change,
                data_status=DataStatus(row["data_status"]),
                drivers=list(row["drivers"]),
                score_coverage=float(row["score_coverage"]),
                source_dates={
                    "market": _to_date(row.get("market_date")),
                    "wikipedia": _to_date(row.get("wikipedia_date")),
                    "finra_short_volume": _to_date(row.get("finra_date")),
                    "social": _to_date(row.get("social_date")),
                },
            )
        )

    latest_payload = LatestPayload(
        generated_at=as_of,
        market_date=market_date,
        score_version=score_config["score_version"],
        symbols=latest_symbols,
    )

    statuses: list[SourceRunStatus] = [
        source_results[name].status for name in ["market", "wikipedia", "finra", "social"]
    ]
    successful = sum(item.hype_score is not None for item in latest_symbols)
    warnings: list[str] = []
    if source_results["social"].status.status == DataStatus.UNAVAILABLE:
        warnings.append("Social attention is not active; Attention weights are renormalized when coverage permits.")
    if source_results["market"].status.status == DataStatus.CACHED:
        warnings.append("Market data uses the last successful real snapshot because live retrieval was unavailable.")
    meta_payload = MetaPayload(
        generated_at=as_of,
        last_successful_overall_update=as_of,
        latest_market_date=market_date,
        score_version=score_config["score_version"],
        universe_size=len(universe),
        successful_symbols=successful,
        failed_symbols=len(universe) - successful,
        sources=statuses,
        warnings=warnings,
        legal_notice=LEGAL_NOTICE,
    )

    history_payloads: list[SymbolHistoryPayload] = []
    source_status_map = {status.source: status for status in statuses}
    universe_map = {item.symbol: item for item in universe}
    latest_map = {item.symbol: item for item in latest_symbols}
    for symbol, config_item in universe_map.items():
        symbol_panel = panel[panel["symbol"] == symbol].sort_values("date") if not panel.empty else pd.DataFrame()
        points: list[HistoryPoint] = []
        for _, row in symbol_panel.iterrows():
            available = sum(
                value is not None and not pd.isna(value)
                for value in [row.get("close"), row.get("pageviews"), row.get("short_volume_ratio"), row.get("mentions")]
            )
            status = DataStatus.PARTIAL if available else DataStatus.UNAVAILABLE
            points.append(
                HistoryPoint(
                    date=row["date"],
                    price=_to_optional_float(row.get("close"), 3),
                    daily_return_pct=_to_optional_float(row.get("daily_return_pct"), 2),
                    volume=_to_optional_int(row.get("volume")),
                    volume_ratio_30d=_to_optional_float(row.get("volume_ratio_30d"), 2),
                    wikipedia_pageviews=_to_optional_int(row.get("pageviews")),
                    wikipedia_change_pct=_to_optional_float(row.get("wikipedia_change_pct"), 1),
                    short_volume_ratio=_to_optional_float(row.get("short_volume_ratio"), 4),
                    attention_score=_to_optional_float(row.get("attention_score"), 1),
                    trading_score=_to_optional_float(row.get("trading_score"), 1),
                    retail_proxy_score=_to_optional_float(row.get("retail_proxy_score"), 1),
                    impact_score=_to_optional_float(row.get("impact_score"), 1),
                    hype_score=_to_optional_float(row.get("hype_score"), 1),
                    confidence_score=None,
                    data_status=status,
                )
            )
        # Replace/add the latest point with the fully asynchronous latest snapshot.
        latest_item = latest_map[symbol]
        if market_date is not None:
            latest_point = HistoryPoint(
                date=market_date,
                price=latest_item.price,
                daily_return_pct=latest_item.daily_return_pct,
                volume=latest_item.volume,
                volume_ratio_30d=latest_item.volume_ratio_30d,
                wikipedia_pageviews=_to_optional_int(
                    scored_latest.loc[scored_latest["symbol"] == symbol, "pageviews"].iloc[0]
                    if "pageviews" in scored_latest and not scored_latest.loc[scored_latest["symbol"] == symbol].empty
                    else None
                ),
                wikipedia_change_pct=_to_optional_float(
                    scored_latest.loc[scored_latest["symbol"] == symbol, "wikipedia_change_pct"].iloc[0]
                    if "wikipedia_change_pct" in scored_latest and not scored_latest.loc[scored_latest["symbol"] == symbol].empty
                    else None,
                    1,
                ),
                short_volume_ratio=_to_optional_float(
                    scored_latest.loc[scored_latest["symbol"] == symbol, "short_volume_ratio"].iloc[0]
                    if "short_volume_ratio" in scored_latest and not scored_latest.loc[scored_latest["symbol"] == symbol].empty
                    else None,
                    4,
                ),
                attention_score=latest_item.attention_score,
                trading_score=latest_item.trading_score,
                retail_proxy_score=latest_item.retail_proxy_score,
                impact_score=latest_item.impact_score,
                hype_score=latest_item.hype_score,
                confidence_score=latest_item.confidence_score,
                data_status=latest_item.data_status,
            )
            points = [point for point in points if point.date != market_date] + [latest_point]
            points.sort(key=lambda point: point.date)
        history_payloads.append(
            SymbolHistoryPayload(
                symbol=symbol,
                company_name=config_item.company_name,
                generated_at=as_of,
                score_version=score_config["score_version"],
                points=points,
                sources=list(source_status_map.values()),
                limitations=[
                    "Hype Score values are comparative proxies and not a percentage of retail ownership.",
                    "Daily source dates can differ because attention data can update when markets are closed.",
                    "FINRA short-sale volume is not the same as short interest and covers specified reported venues.",
                ],
            )
        )

    report = UpdateReport(
        generated_at=as_of,
        score_version=score_config["score_version"],
        market_date=market_date,
        universe_size=len(universe),
        successful_symbols=successful,
        failed_symbols=len(universe) - successful,
        validation_warnings=[],
        sources=statuses,
    )
    return latest_payload, meta_payload, history_payloads, report


def persist_outputs(
    latest: LatestPayload,
    meta: MetaPayload,
    histories: list[SymbolHistoryPayload],
    report: UpdateReport,
) -> None:
    public = ROOT / "frontend" / "public" / "data"
    processed = ROOT / "data" / "processed"
    history_dir = ROOT / "data" / "history"
    metadata_dir = ROOT / "data" / "metadata"
    public_history = public / "history"
    for directory in [public, processed, history_dir, metadata_dir, public_history]:
        directory.mkdir(parents=True, exist_ok=True)

    _write_json(public / "latest.json", latest)
    _write_json(public / "meta.json", meta)
    _write_json(processed / "latest.json", latest)
    _write_json(metadata_dir / "meta.json", meta)
    for history in histories:
        _write_json(public_history / f"{history.symbol}.json", history)
        _write_json(history_dir / f"{history.symbol}.json", history)

    report_markdown = [
        "# Hypeboard update report",
        "",
        f"- Generated: {report.generated_at.isoformat()}",
        f"- Market date: {report.market_date or 'unavailable'}",
        f"- Score version: {report.score_version}",
        f"- Universe: {report.universe_size}",
        f"- Symbols with a Hype Score: {report.successful_symbols}",
        f"- Symbols without a Hype Score: {report.failed_symbols}",
        "",
        "## Source status",
        "",
        "| Source | Status | Records | Symbols | Last observation | Note |",
        "|---|---:|---:|---:|---|---|",
    ]
    for status in report.sources:
        report_markdown.append(
            f"| {status.source} | {status.status.value} | {status.records} | "
            f"{status.symbols_updated} | {status.last_observation_at or '—'} | {status.delay_note} |"
        )
    if report.validation_warnings:
        report_markdown.extend(["", "## Validation warnings", ""])
        report_markdown.extend(f"- {warning}" for warning in report.validation_warnings)
    (metadata_dir / "update-report.md").write_text("\n".join(report_markdown) + "\n", encoding="utf-8")


def run(*, as_of: datetime, offline: bool) -> UpdateReport:
    universe, score_config = load_configuration()
    if os.getenv("HYPEBOARD_DEMO_MODE", "false").lower() == "true":
        raise RuntimeError("Demo mode is intentionally not implemented in the production update path.")
    adapters = {
        "market": MarketDataAdapter(ROOT),
        "wikipedia": WikipediaPageviewsAdapter(ROOT),
        "finra": FinraShortVolumeAdapter(ROOT),
        "social": SocialAttentionAdapter(ROOT),
    }
    results = {
        name: fetch_source_safely(adapter, universe, as_of, offline=offline)
        for name, adapter in adapters.items()
    }
    latest, meta, histories, report = create_outputs(
        universe, score_config, results, as_of
    )
    warnings = validate_payloads(
        latest, meta, histories, expected_universe_size=len(universe)
    )
    report.validation_warnings.extend(warnings)
    persist_outputs(latest, meta, histories, report)
    export_schemas(ROOT)
    LOGGER.info(
        "pipeline completed",
        extra={
            "market_date": str(report.market_date),
            "successful_symbols": report.successful_symbols,
            "failed_symbols": report.failed_symbols,
            "offline": offline,
        },
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Hypeboard data pipeline")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Do not access the network; use the last cache or bundled real snapshot.",
    )
    parser.add_argument(
        "--as-of",
        help="ISO-8601 generation timestamp. Defaults to the current UTC time.",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()
    as_of = date_parser.isoparse(args.as_of) if args.as_of else datetime.now(UTC)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=UTC)
    run(as_of=as_of, offline=args.offline)


if __name__ == "__main__":
    main()
