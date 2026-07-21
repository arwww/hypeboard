from __future__ import annotations

import io
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from pipeline.models import DataStatus, SymbolConfig
from pipeline.sources.base import AdapterResult, SourceAdapter

LOGGER = logging.getLogger(__name__)


class FinraShortVolumeAdapter(SourceAdapter):
    source_name = "finra_short_volume"
    delay_note = (
        "FINRA consolidated TRF/ADF daily short-sale volume, normally posted by 18:00 ET. "
        "It is off-exchange reported volume and is not short interest."
    )
    endpoint = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date}.txt"

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
        symbols = {item.symbol for item in universe}
        frames: list[pd.DataFrame] = []
        errors: list[str] = []
        for offset in range(0, 48):
            candidate = as_of.date() - timedelta(days=offset)
            if candidate.weekday() >= 5:
                continue
            try:
                response = self.request(
                    self.endpoint.format(date=candidate.strftime("%Y%m%d"))
                )
                frame = self._parse_file(response.text, symbols)
                if not frame.empty:
                    frames.append(frame)
            except Exception as exc:
                # Holidays and not-yet-posted dates are expected; isolate them.
                errors.append(f"{candidate.isoformat()}: {exc}")
        if not frames:
            return self.cached_or_unavailable(
                retrieved_at=as_of,
                error="no FINRA files available in the lookback window",
                seed_loader=self._load_seed,
            )
        data = pd.concat(frames, ignore_index=True).drop_duplicates(["symbol", "date"])
        data["retrieved_at"] = as_of.isoformat()
        data["source_status"] = DataStatus.FRESH.value
        self.save_cache(data, as_of)
        return AdapterResult(
            data=data,
            status=self.status(
                status=DataStatus.FRESH,
                retrieved_at=as_of,
                data=data,
                error=None,
            ),
        )

    @staticmethod
    def _parse_file(text: str, symbols: set[str]) -> pd.DataFrame:
        lines = [line for line in text.splitlines() if line.count("|") >= 5]
        if not lines:
            return pd.DataFrame()
        frame = pd.read_csv(io.StringIO("\n".join(lines)), sep="|")
        frame = frame[frame["Symbol"].isin(symbols)].copy()
        if frame.empty:
            return frame
        frame = frame.rename(
            columns={
                "Date": "date",
                "Symbol": "symbol",
                "ShortVolume": "short_volume",
                "ShortExemptVolume": "short_exempt_volume",
                "TotalVolume": "finra_total_volume",
                "Market": "market",
            }
        )
        frame["date"] = pd.to_datetime(
            frame["date"].astype(str), format="%Y%m%d", errors="coerce"
        ).dt.date
        for column in ["short_volume", "short_exempt_volume", "finra_total_volume"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=["date", "short_volume", "finra_total_volume"])
        frame["short_volume_ratio"] = frame["short_volume"] / frame[
            "finra_total_volume"
        ].replace(0, pd.NA)
        frame["source"] = "finra_consolidated_nms"
        return frame[
            [
                "symbol",
                "date",
                "short_volume",
                "short_exempt_volume",
                "finra_total_volume",
                "short_volume_ratio",
                "market",
                "source",
            ]
        ]

    def _load_seed(self) -> pd.DataFrame:
        seed_dir = self.root / "data" / "raw" / "seed" / "finra"
        symbols = {
            item["symbol"]
            for item in __import__("json").loads(
                (self.root / "pipeline" / "config" / "universe.json").read_text()
            )
        }
        frames: list[pd.DataFrame] = []
        for path in sorted(seed_dir.glob("CNMSshvol*.txt")):
            try:
                frames.append(self._parse_file(path.read_text(encoding="utf-8"), symbols))
            except OSError:
                LOGGER.exception("failed to read bundled FINRA file", extra={"path": str(path)})
        if not frames:
            return pd.DataFrame()
        data = pd.concat(frames, ignore_index=True).drop_duplicates(["symbol", "date"])
        data["retrieved_at"] = "2026-07-19T23:37:00+02:00"
        return data
