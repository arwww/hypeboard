from __future__ import annotations

import io
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from pipeline.models import DataStatus, SymbolConfig
from pipeline.sources.base import AdapterResult, SourceAdapter

LOGGER = logging.getLogger(__name__)


class MarketDataAdapter(SourceAdapter):
    """Daily OHLCV adapter.

    The default implementation uses Stooq's public CSV download endpoint. Stooq does
    not publish an API SLA or a documented per-minute quota for this endpoint. The
    adapter therefore spaces requests, uses caching and treats it as a best-effort
    delayed EOD source. Provider-specific code is contained in this module.
    """

    source_name = "market_data"
    delay_note = (
        "Daily end-of-day data. Provider availability and adjustments may be delayed; "
        "Stooq exposes no official API SLA for the CSV endpoint."
    )
    endpoint = "https://stooq.com/q/d/l/"

    def __init__(self, root: Path, user_agent: str | None = None) -> None:
        super().__init__(root, user_agent)
        self.provider = os.getenv("HYPEBOARD_MARKET_PROVIDER", "stooq").lower()
        self.request_delay = float(
            os.getenv("HYPEBOARD_MARKET_REQUEST_DELAY_SECONDS", "0.35")
        )

    def fetch(
        self,
        universe: list[SymbolConfig],
        as_of: datetime,
        offline: bool = False,
    ) -> AdapterResult:
        if offline:
            return self.cached_or_unavailable(
                retrieved_at=as_of,
                error="offline mode",
                seed_loader=self._load_seed,
            )
        if self.provider != "stooq":
            return self.cached_or_unavailable(
                retrieved_at=as_of,
                error=f"unsupported market provider: {self.provider}",
                seed_loader=self._load_seed,
            )
        try:
            start = (as_of.date() - timedelta(days=220)).strftime("%Y%m%d")
            end = as_of.date().strftime("%Y%m%d")
            frames: list[pd.DataFrame] = []
            errors: list[str] = []
            for index, config in enumerate(universe):
                try:
                    response = self.request(
                        self.endpoint,
                        params={
                            "s": f"{config.symbol.lower()}.us",
                            "i": "d",
                            "d1": start,
                            "d2": end,
                        },
                    )
                    frame = self._parse_csv(response.text, config.symbol)
                    if frame.empty:
                        raise ValueError("provider returned no rows")
                    frames.append(frame)
                except Exception as exc:  # isolated per symbol by design
                    errors.append(f"{config.symbol}: {exc}")
                    LOGGER.warning(
                        "market symbol update failed",
                        extra={"source": self.source_name, "symbol": config.symbol, "error": str(exc)},
                    )
                if index < len(universe) - 1:
                    time.sleep(self.request_delay)
            if not frames:
                raise RuntimeError("no market symbols were updated")
            data = pd.concat(frames, ignore_index=True)
            data["retrieved_at"] = as_of.isoformat()
            data["source_status"] = DataStatus.FRESH.value
            self.save_cache(data, as_of)
            status_value = DataStatus.PARTIAL if errors else DataStatus.FRESH
            return AdapterResult(
                data=data,
                status=self.status(
                    status=status_value,
                    retrieved_at=as_of,
                    data=data,
                    error="; ".join(errors[:8]) if errors else None,
                ),
            )
        except Exception as exc:
            return self.cached_or_unavailable(
                retrieved_at=as_of,
                error=exc,
                seed_loader=self._load_seed,
            )

    @staticmethod
    def _parse_csv(text: str, symbol: str) -> pd.DataFrame:
        frame = pd.read_csv(io.StringIO(text))
        expected = {"Date", "Open", "High", "Low", "Close", "Volume"}
        if not expected.issubset(frame.columns):
            raise ValueError(f"unexpected Stooq schema: {list(frame.columns)}")
        frame = frame.rename(columns=str.lower)
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
        for column in ["open", "high", "low", "close", "volume"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=["date", "close", "volume"])
        frame["volume"] = frame["volume"].round().astype("int64")
        frame["symbol"] = symbol
        frame["source"] = "stooq"
        return frame[
            ["symbol", "date", "open", "high", "low", "close", "volume", "source"]
        ]

    def _load_seed(self) -> pd.DataFrame:
        path = self.root / "data" / "raw" / "seed" / "market_snapshot_2026-07-17.csv"
        if not path.exists():
            return pd.DataFrame()
        frame = pd.read_csv(path)
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
        frame["source"] = "bundled_real_market_snapshot"
        frame["retrieved_at"] = "2026-07-19T23:37:00+02:00"
        return frame
