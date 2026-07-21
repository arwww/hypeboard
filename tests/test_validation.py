from datetime import date, datetime, timezone

import pytest

from pipeline.models import (
    DataStatus,
    LatestPayload,
    LatestSymbol,
    MetaPayload,
    SourceRunStatus,
    SymbolHistoryPayload,
)
from pipeline.validation.data_quality import DataQualityError, validate_payloads


def source_status() -> SourceRunStatus:
    return SourceRunStatus(
        source="test",
        status=DataStatus.FRESH,
        last_observation_at=date(2026, 7, 17),
        retrieved_at=datetime(2026, 7, 19, tzinfo=timezone.utc),
        records=1,
        symbols_updated=1,
        delay_note="test",
    )


def symbol(symbol: str, score: float) -> LatestSymbol:
    return LatestSymbol(
        symbol=symbol,
        company_name=symbol,
        exchange="NASDAQ",
        sector="Test",
        price=10,
        daily_return_pct=1,
        volume=1000,
        volume_ratio_30d=1,
        attention_score=score,
        trading_score=score,
        retail_proxy_score=score,
        impact_score=score,
        hype_score=score,
        confidence_score=80,
        rank=1,
        rank_change=0,
        data_status=DataStatus.FRESH,
        drivers=[],
        score_coverage=1,
        source_dates={"market": date(2026, 7, 17)},
    )


def test_score_model_rejects_out_of_range_score() -> None:
    with pytest.raises(ValueError):
        symbol("AAA", 101)


def test_duplicate_symbols_are_rejected() -> None:
    generated = datetime(2026, 7, 19, tzinfo=timezone.utc)
    latest = LatestPayload(
        generated_at=generated,
        market_date=date(2026, 7, 17),
        score_version="1.0.0",
        symbols=[symbol("AAA", 60), symbol("AAA", 50)],
    )
    meta = MetaPayload(
        generated_at=generated,
        last_successful_overall_update=generated,
        latest_market_date=date(2026, 7, 17),
        score_version="1.0.0",
        universe_size=2,
        successful_symbols=2,
        failed_symbols=0,
        sources=[source_status()],
        warnings=[],
        legal_notice="test",
    )
    histories = [
        SymbolHistoryPayload(
            symbol="AAA",
            company_name="AAA",
            generated_at=generated,
            score_version="1.0.0",
            points=[],
            sources=[source_status()],
            limitations=[],
        )
    ]
    with pytest.raises(DataQualityError, match="duplicate symbols"):
        validate_payloads(latest, meta, histories, expected_universe_size=2)
