from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Iterable

from pipeline.models import LatestPayload, MetaPayload, SymbolHistoryPayload


class DataQualityError(ValueError):
    pass


def validate_payloads(
    latest: LatestPayload,
    meta: MetaPayload,
    histories: Iterable[SymbolHistoryPayload],
    *,
    expected_universe_size: int,
) -> list[str]:
    warnings: list[str] = []
    symbols = [item.symbol for item in latest.symbols]
    duplicates = [symbol for symbol, count in Counter(symbols).items() if count > 1]
    if duplicates:
        raise DataQualityError(f"duplicate symbols: {duplicates}")
    if len(symbols) != expected_universe_size:
        raise DataQualityError(
            f"expected {expected_universe_size} symbols, generated {len(symbols)}"
        )
    if meta.universe_size != expected_universe_size:
        raise DataQualityError("meta universe size does not match configuration")

    generated = latest.generated_at
    if not isinstance(generated, datetime):
        raise DataQualityError("latest.generated_at is missing")

    scored = [item.hype_score for item in latest.symbols if item.hype_score is not None]
    if not scored:
        raise DataQualityError("no Hype Scores were generated")
    if max(scored) - min(scored) < 1:
        warnings.append("Hype Score distribution is unusually narrow.")

    extreme_rank_changes = [
        item.symbol
        for item in latest.symbols
        if item.rank_change is not None and abs(item.rank_change) > expected_universe_size * 0.75
    ]
    if extreme_rank_changes:
        warnings.append(
            "Extreme daily rank changes detected: " + ", ".join(extreme_rank_changes)
        )

    for item in latest.symbols:
        if item.price is not None and (item.price <= 0 or item.price > 1_000_000):
            raise DataQualityError(f"unrealistic price for {item.symbol}: {item.price}")
        if item.volume is not None and (item.volume < 0 or item.volume > 100_000_000_000):
            raise DataQualityError(f"unrealistic volume for {item.symbol}: {item.volume}")
        if item.confidence_score < 35:
            warnings.append(f"{item.symbol} has low confidence ({item.confidence_score:.0f}).")

    history_symbols: set[str] = set()
    for history in histories:
        history_symbols.add(history.symbol)
        dates = [point.date for point in history.points]
        if len(dates) != len(set(dates)):
            raise DataQualityError(f"duplicate history date for {history.symbol}")
        if dates != sorted(dates):
            raise DataQualityError(f"history is not sorted for {history.symbol}")
    if history_symbols != set(symbols):
        raise DataQualityError("history files do not cover the full universe")
    return warnings
