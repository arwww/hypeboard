from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from pipeline.models import DataStatus, SymbolConfig
from pipeline.sources.base import AdapterResult, SourceAdapter

LOGGER = logging.getLogger(__name__)


class MarketDataAdapter(SourceAdapter):
    """Daily OHLCV adapter using Yahoo Finance through yfinance."""

    source_name = "market_data"

    delay_note = (
        "Daily end-of-day market data retrieved through yfinance. "
        "Availability and adjustments can be delayed."
    )

    def __init__(self, root: Path, user_agent: str | None = None) -> None:
        super().__init__(root, user_agent)

        self.provider = os.getenv(
            "HYPEBOARD_MARKET_PROVIDER",
            "yfinance",
        ).lower()

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

        if self.provider != "yfinance":
            return self.cached_or_unavailable(
                retrieved_at=as_of,
                error=f"unsupported market provider: {self.provider}",
                seed_loader=self._load_seed,
            )

        try:
            # 220 calendar days provide substantially more than
            # the required 30 trading observations.
            start_date = as_of.date() - timedelta(days=220)

            # yfinance treats the end date as exclusive.
            end_date = as_of.date() + timedelta(days=1)

            symbols = [config.symbol for config in universe]

            raw = yf.download(
                tickers=symbols,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                interval="1d",
                group_by="ticker",
                auto_adjust=False,
                actions=False,
                threads=True,
                progress=False,
                repair=True,
                timeout=30,
                multi_level_index=True,
            )

            if raw is None or raw.empty:
                raise RuntimeError("yfinance returned no market data")

            frames: list[pd.DataFrame] = []
            errors: list[str] = []

            for config in universe:
                try:
                    symbol = config.symbol

                    if isinstance(raw.columns, pd.MultiIndex):
                        available_symbols = raw.columns.get_level_values(0)

                        if symbol not in available_symbols:
                            raise ValueError(
                                f"symbol is missing from yfinance response: {symbol}"
                            )

                        frame = raw[symbol].copy()
                    else:
                        # This can occur when only one ticker was requested.
                        frame = raw.copy()

                    frame = frame.reset_index()

                    frame.columns = [
                        str(column).strip().lower().replace(" ", "_")
                        for column in frame.columns
                    ]

                    if "datetime" in frame.columns and "date" not in frame.columns:
                        frame = frame.rename(columns={"datetime": "date"})

                    expected = {
                        "date",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                    }

                    missing = expected.difference(frame.columns)

                    if missing:
                        raise ValueError(
                            f"missing yfinance columns: {sorted(missing)}"
                        )

                    frame["date"] = pd.to_datetime(
                        frame["date"],
                        errors="coerce",
                    ).dt.date

                    for column in [
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                    ]:
                        frame[column] = pd.to_numeric(
                            frame[column],
                            errors="coerce",
                        )

                    frame = frame.dropna(
                        subset=["date", "close", "volume"]
                    )

                    if frame.empty:
                        raise ValueError(
                            "yfinance returned no valid OHLCV rows"
                        )

                    frame["volume"] = (
                        frame["volume"]
                        .round()
                        .astype("int64")
                    )

                    frame["symbol"] = symbol
                    frame["source"] = "yahoo_finance_via_yfinance"

                    frames.append(
                        frame[
                            [
                                "symbol",
                                "date",
                                "open",
                                "high",
                                "low",
                                "close",
                                "volume",
                                "source",
                            ]
                        ]
                    )

                except Exception as exc:
                    errors.append(f"{config.symbol}: {exc}")

                    LOGGER.warning(
                        "market symbol update failed",
                        extra={
                            "source": self.source_name,
                            "symbol": config.symbol,
                            "error": str(exc),
                        },
                    )

            if not frames:
                raise RuntimeError(
                    "no market symbols were successfully updated"
                )

            data = pd.concat(frames, ignore_index=True)

            data["retrieved_at"] = as_of.isoformat()
            data["source_status"] = DataStatus.FRESH.value

            self.save_cache(data, as_of)

            status_value = (
                DataStatus.PARTIAL
                if errors
                else DataStatus.FRESH
            )

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
            LOGGER.exception(
                "yfinance market update failed",
                extra={
                    "source": self.source_name,
                    "error": str(exc),
                },
            )

            return self.cached_or_unavailable(
                retrieved_at=as_of,
                error=exc,
                seed_loader=self._load_seed,
            )

    def _load_seed(self) -> pd.DataFrame:
        path = (
            self.root
            / "data"
            / "raw"
            / "seed"
            / "market_snapshot_2026-07-17.csv"
        )

        if not path.exists():
            return pd.DataFrame()

        frame = pd.read_csv(path)

        frame["date"] = pd.to_datetime(
            frame["date"],
            errors="coerce",
        ).dt.date

        frame["source"] = "bundled_real_market_snapshot"
        frame["retrieved_at"] = "2026-07-19T23:37:00+02:00"

        return frame