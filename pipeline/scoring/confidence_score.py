from __future__ import annotations

from datetime import date

import pandas as pd

from pipeline.scoring.normalization import clipped


def _freshness_points(source_date: date | None, as_of: date, fresh_days: int, stale_days: int) -> float:
    if source_date is None or pd.isna(source_date):
        return 0.0
    if not isinstance(source_date, date):
        source_date = pd.to_datetime(source_date).date()
    age = max((as_of - source_date).days, 0)
    if age <= fresh_days:
        return 100.0
    if age >= stale_days:
        return 0.0
    return 100.0 * (stale_days - age) / (stale_days - fresh_days)


def calculate_confidence(
    *,
    row: pd.Series,
    as_of: date,
    history_counts: dict[str, int],
    config: dict,
) -> tuple[float, dict[str, float]]:
    expected = {
        "price": row.get("close"),
        "volume": row.get("volume"),
        "wikipedia": row.get("pageviews"),
        "finra": row.get("short_volume_ratio"),
        "social": row.get("mentions"),
    }
    # Social is expected but lower-quality; its absence does not collapse confidence.
    completeness_weights = {"price": 0.25, "volume": 0.20, "wikipedia": 0.25, "finra": 0.20, "social": 0.10}
    completeness = 100 * sum(
        completeness_weights[name]
        for name, value in expected.items()
        if value is not None and not pd.isna(value)
    )

    def safe_date(value):
        if value is None or pd.isna(value):
            return None
        return value if isinstance(value, date) else pd.to_datetime(value).date()

    market_date = safe_date(row.get("market_date"))
    wiki_date = safe_date(row.get("wikipedia_date"))
    finra_date = safe_date(row.get("finra_date"))
    social_date = safe_date(row.get("social_date"))
    freshness_values = [
        _freshness_points(market_date, as_of, 3, 10),
        _freshness_points(wiki_date, as_of, 2, 7),
        _freshness_points(finra_date, as_of, 3, 10),
    ]
    if social_date:
        freshness_values.append(_freshness_points(social_date, as_of, 2, 7))
    freshness = sum(freshness_values) / len(freshness_values)

    available_sources = sum(
        [
            market_date is not None,
            wiki_date is not None,
            finra_date is not None,
            social_date is not None,
        ]
    )
    independent_sources = min(100.0, available_sources / 4 * 100)

    observations = [
        min(history_counts.get("market", 0), 30) / 30,
        min(history_counts.get("wikipedia", 0), 30) / 30,
        min(history_counts.get("finra", 0), 20) / 20,
    ]
    history_length = sum(observations) / len(observations) * 100

    proxy_quality = 0.0
    proxy_quality += 35 if market_date else 0
    proxy_quality += 30 if wiki_date else 0
    proxy_quality += 25 if finra_date else 0
    proxy_quality += 10 if social_date else 0

    parts = {
        "data_completeness": completeness,
        "freshness": freshness,
        "independent_sources": independent_sources,
        "history_length": history_length,
        "proxy_quality": proxy_quality,
    }
    weights = config["confidence"]
    score = sum(parts[name] * weights[name] for name in parts) / sum(weights.values())
    return round(clipped(score) or 0.0, 1), {key: round(value, 1) for key, value in parts.items()}
