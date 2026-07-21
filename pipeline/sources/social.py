from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from pipeline.models import DataStatus, SymbolConfig
from pipeline.sources.base import AdapterResult, SourceAdapter


class SocialAttentionAdapter(SourceAdapter):
    """Optional adapter for a user-supplied public, legal JSON feed.

    Hypeboard deliberately ships without scraping logged-in platforms or reverse
    engineering broker/social applications. When `HYPEBOARD_SOCIAL_DATA_URL` is
    unset, the source is explicitly unavailable and score weights are handled by
    the minimum-coverage rules.
    """

    source_name = "social"
    delay_note = "No public social provider is active unless HYPEBOARD_SOCIAL_DATA_URL is configured."

    def __init__(self, root: Path, user_agent: str | None = None) -> None:
        super().__init__(root, user_agent)
        self.endpoint = os.getenv("HYPEBOARD_SOCIAL_DATA_URL", "").strip()

    def fetch(
        self,
        universe: list[SymbolConfig],
        as_of: datetime,
        offline: bool = False,
    ) -> AdapterResult:
        if offline or not self.endpoint:
            error = "offline mode" if offline else "no public social data endpoint configured"
            return AdapterResult(
                data=pd.DataFrame(),
                status=self.status(
                    status=DataStatus.UNAVAILABLE,
                    retrieved_at=as_of,
                    data=pd.DataFrame(),
                    error=error,
                ),
            )
        try:
            payload = self.request(self.endpoint).json()
            frame = pd.DataFrame(payload.get("records", payload))
            required = {"symbol", "date", "mentions"}
            if not required.issubset(frame.columns):
                raise ValueError(f"social endpoint must provide {sorted(required)}")
            valid_symbols = {item.symbol for item in universe}
            frame = frame[frame["symbol"].isin(valid_symbols)].copy()
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
            frame["mentions"] = pd.to_numeric(frame["mentions"], errors="coerce")
            frame = frame.dropna(subset=["date", "mentions"])
            frame["source"] = "configured_public_social_feed"
            frame["retrieved_at"] = as_of.isoformat()
            frame["source_status"] = DataStatus.FRESH.value
            self.save_cache(frame, as_of)
            return AdapterResult(
                data=frame,
                status=self.status(
                    status=DataStatus.FRESH, retrieved_at=as_of, data=frame
                ),
            )
        except Exception as exc:
            return self.cached_or_unavailable(retrieved_at=as_of, error=exc)
