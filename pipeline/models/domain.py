from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataStatus(StrEnum):
    FRESH = "fresh"
    CACHED = "cached"
    STALE = "stale"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class SymbolConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9.-]{0,13}$")
    company_name: str
    exchange: str
    sector: str
    wikipedia_page: str
    aliases: list[str] = Field(default_factory=list)
    active: bool = True


class SourceObservation(BaseModel):
    model_config = ConfigDict(extra="allow")

    symbol: str
    metric: str
    value: float | int | None
    observed_at: date | datetime
    source: str
    retrieved_at: datetime
    status: DataStatus
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceRunStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    status: DataStatus
    last_observation_at: date | datetime | None = None
    retrieved_at: datetime
    records: int = 0
    symbols_updated: int = 0
    error: str | None = None
    delay_note: str


class ScoreBreakdown(BaseModel):
    attention: float | None = None
    trading: float | None = None
    retail_proxy: float | None = None
    impact: float | None = None

    @field_validator("attention", "trading", "retail_proxy", "impact")
    @classmethod
    def validate_optional_score(cls, value: float | None) -> float | None:
        if value is not None and not 0 <= value <= 100:
            raise ValueError("score must be between 0 and 100")
        return value


class LatestSymbol(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    company_name: str
    exchange: str
    sector: str
    price: float | None
    daily_return_pct: float | None
    volume: int | None
    volume_ratio_30d: float | None
    attention_score: float | None
    trading_score: float | None
    retail_proxy_score: float | None
    impact_score: float | None
    hype_score: float | None
    hype_score_change: float | None = None
    confidence_score: float
    rank: int | None
    rank_change: int | None
    data_status: DataStatus
    drivers: list[str]
    score_coverage: float = Field(ge=0, le=1)
    source_dates: dict[str, date | None]

    @field_validator(
        "attention_score",
        "trading_score",
        "retail_proxy_score",
        "impact_score",
        "hype_score",
        "confidence_score",
    )
    @classmethod
    def validate_score(cls, value: float | None) -> float | None:
        if value is not None and not 0 <= value <= 100:
            raise ValueError("score must be between 0 and 100")
        return value


class LatestPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    market_date: date | None
    score_version: str
    symbols: list[LatestSymbol]


class HistoryPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    price: float | None = None
    daily_return_pct: float | None = None
    volume: int | None = None
    volume_ratio_30d: float | None = None
    wikipedia_pageviews: int | None = None
    wikipedia_change_pct: float | None = None
    short_volume_ratio: float | None = None
    attention_score: float | None = None
    trading_score: float | None = None
    retail_proxy_score: float | None = None
    impact_score: float | None = None
    hype_score: float | None = None
    confidence_score: float | None = None
    data_status: DataStatus

    @field_validator(
        "attention_score",
        "trading_score",
        "retail_proxy_score",
        "impact_score",
        "hype_score",
        "confidence_score",
    )
    @classmethod
    def validate_history_score(cls, value: float | None) -> float | None:
        if value is not None and not 0 <= value <= 100:
            raise ValueError("score must be between 0 and 100")
        return value


class SymbolHistoryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    company_name: str
    generated_at: datetime
    score_version: str
    points: list[HistoryPoint]
    sources: list[SourceRunStatus]
    limitations: list[str]


class MetaPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    last_successful_overall_update: datetime
    latest_market_date: date | None
    score_version: str
    universe_size: int
    successful_symbols: int
    failed_symbols: int
    sources: list[SourceRunStatus]
    warnings: list[str]
    legal_notice: str


class UpdateReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    score_version: str
    market_date: date | None
    universe_size: int
    successful_symbols: int
    failed_symbols: int
    validation_warnings: list[str]
    sources: list[SourceRunStatus]
