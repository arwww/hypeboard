from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import pandas as pd

from pipeline.models import DataStatus, SymbolConfig
from pipeline.sources.base import AdapterResult, SourceAdapter

LOGGER = logging.getLogger(__name__)


class WikipediaPageviewsAdapter(SourceAdapter):
    source_name = "wikipedia"
    delay_note = "Daily Wikimedia Pageviews; the newest complete UTC day can arrive with a short delay."
    endpoint = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        "en.wikipedia.org/all-access/user/{article}/daily/{start}/{end}"
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
        try:
            start = (as_of.date() - timedelta(days=120)).strftime("%Y%m%d00")
            end = (as_of.date() - timedelta(days=1)).strftime("%Y%m%d00")
            rows: list[dict[str, object]] = []
            errors: list[str] = []
            for config in universe:
                try:
                    article = quote(config.wikipedia_page.replace(" ", "_"), safe="")
                    response = self.request(
                        self.endpoint.format(article=article, start=start, end=end)
                    )
                    for item in response.json().get("items", []):
                        rows.append(
                            {
                                "symbol": config.symbol,
                                "date": datetime.strptime(item["timestamp"], "%Y%m%d00").date(),
                                "pageviews": int(item["views"]),
                                "article": item["article"],
                                "source": "wikimedia_pageviews",
                            }
                        )
                except Exception as exc:
                    errors.append(f"{config.symbol}: {exc}")
                    LOGGER.warning(
                        "wikipedia symbol update failed",
                        extra={"source": self.source_name, "symbol": config.symbol, "error": str(exc)},
                    )
            data = pd.DataFrame(rows)
            if data.empty:
                raise RuntimeError("no Wikimedia observations were updated")
            data["retrieved_at"] = as_of.isoformat()
            data["source_status"] = DataStatus.FRESH.value
            self.save_cache(data, as_of)
            return AdapterResult(
                data=data,
                status=self.status(
                    status=DataStatus.PARTIAL if errors else DataStatus.FRESH,
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

    def _load_seed(self) -> pd.DataFrame:
        path = self.root / "data" / "raw" / "seed" / "wikipedia_pageviews.csv"
        if not path.exists():
            return pd.DataFrame()
        frame = pd.read_csv(path)
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
        frame["source"] = "wikimedia_pageviews"
        frame["retrieved_at"] = "2026-07-19T23:37:00+02:00"
        return frame
