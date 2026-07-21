from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests

from pipeline.models import DataStatus, SourceRunStatus, SymbolConfig

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class AdapterResult:
    data: pd.DataFrame
    status: SourceRunStatus


class SourceAdapter(ABC):
    source_name: str
    delay_note: str

    def __init__(self, root: Path, user_agent: str | None = None) -> None:
        self.root = root
        self.raw_dir = root / "data" / "raw" / self.source_name
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = float(os.getenv("HYPEBOARD_REQUEST_TIMEOUT_SECONDS", "20"))
        self.retries = int(os.getenv("HYPEBOARD_REQUEST_RETRIES", "3"))
        self.backoff = float(os.getenv("HYPEBOARD_REQUEST_BACKOFF_SECONDS", "1.0"))
        self.user_agent = user_agent or os.getenv(
            "HYPEBOARD_USER_AGENT",
            "Hypeboard/1.0 (public-data research dashboard; contact not configured)",
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/json,text/plain,text/csv,*/*",
            }
        )

    @abstractmethod
    def fetch(
        self,
        universe: list[SymbolConfig],
        as_of: datetime,
        offline: bool = False,
    ) -> AdapterResult:
        raise NotImplementedError

    def request(self, url: str, *, params: dict[str, Any] | None = None) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise requests.HTTPError(
                        f"retryable response {response.status_code}", response=response
                    )
                response.raise_for_status()
                return response
            except (requests.RequestException, TimeoutError) as exc:
                last_error = exc
                if attempt == self.retries:
                    break
                sleep_seconds = self.backoff * (2 ** (attempt - 1))
                LOGGER.warning(
                    "source request failed; retrying",
                    extra={
                        "source": self.source_name,
                        "url": url,
                        "attempt": attempt,
                        "sleep_seconds": sleep_seconds,
                        "error": str(exc),
                    },
                )
                time.sleep(sleep_seconds)
        raise RuntimeError(f"{self.source_name} request failed: {last_error}") from last_error

    def save_cache(self, data: pd.DataFrame, as_of: datetime) -> Path:
        path = self.raw_dir / f"{as_of.date().isoformat()}.json"
        records = json.loads(data.to_json(orient="records", date_format="iso"))
        payload = {
            "source": self.source_name,
            "retrieved_at": as_of.astimezone(UTC).isoformat(),
            "records": records,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def load_latest_cache(self) -> tuple[pd.DataFrame, Path] | None:
        candidates = sorted(self.raw_dir.glob("*.json"), reverse=True)
        for path in candidates:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                return pd.DataFrame(payload.get("records", [])), path
            except (OSError, json.JSONDecodeError, TypeError):
                LOGGER.exception(
                    "failed to read source cache",
                    extra={"source": self.source_name, "path": str(path)},
                )
        return None

    def status(
        self,
        *,
        status: DataStatus,
        retrieved_at: datetime,
        data: pd.DataFrame | None = None,
        error: str | None = None,
        date_column: str = "date",
    ) -> SourceRunStatus:
        frame = data if data is not None else pd.DataFrame()
        last_observation: date | datetime | None = None
        if not frame.empty and date_column in frame.columns:
            parsed = pd.to_datetime(frame[date_column], errors="coerce").dropna()
            if not parsed.empty:
                last_observation = parsed.max().date()
        symbols_updated = (
            int(frame["symbol"].nunique()) if not frame.empty and "symbol" in frame else 0
        )
        return SourceRunStatus(
            source=self.source_name,
            status=status,
            last_observation_at=last_observation,
            retrieved_at=retrieved_at,
            records=len(frame),
            symbols_updated=symbols_updated,
            error=error,
            delay_note=self.delay_note,
        )

    def cached_or_unavailable(
        self,
        *,
        retrieved_at: datetime,
        error: Exception | str,
        seed_loader: Callable[[], pd.DataFrame] | None = None,
    ) -> AdapterResult:
        cached = self.load_latest_cache()
        if cached is not None:
            data, path = cached
            LOGGER.warning(
                "using last successful source cache",
                extra={
                    "source": self.source_name,
                    "cache": str(path),
                    "error": str(error),
                },
            )
            data["source_status"] = DataStatus.CACHED.value
            return AdapterResult(
                data=data,
                status=self.status(
                    status=DataStatus.CACHED,
                    retrieved_at=retrieved_at,
                    data=data,
                    error=str(error),
                ),
            )
        if seed_loader is not None:
            seed_data = seed_loader()
            if not seed_data.empty:
                seed_data["source_status"] = DataStatus.CACHED.value
                return AdapterResult(
                    data=seed_data,
                    status=self.status(
                        status=DataStatus.CACHED,
                        retrieved_at=retrieved_at,
                        data=seed_data,
                        error=f"live retrieval failed; bundled real snapshot used: {error}",
                    ),
                )
        empty = pd.DataFrame()
        return AdapterResult(
            data=empty,
            status=self.status(
                status=DataStatus.UNAVAILABLE,
                retrieved_at=retrieved_at,
                data=empty,
                error=str(error),
            ),
        )
