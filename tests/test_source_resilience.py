from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from pipeline.models import DataStatus, SymbolConfig
from pipeline.sources.base import AdapterResult, SourceAdapter


class DummyAdapter(SourceAdapter):
    source_name = "dummy"
    delay_note = "test source"

    def fetch(
        self,
        universe: list[SymbolConfig],
        as_of: datetime,
        offline: bool = False,
    ) -> AdapterResult:
        return self.cached_or_unavailable(retrieved_at=as_of, error="provider down")


def test_failed_source_uses_last_successful_cache(tmp_path: Path) -> None:
    adapter = DummyAdapter(tmp_path)
    as_of = datetime(2026, 7, 19, tzinfo=timezone.utc)
    cached = pd.DataFrame(
        [{"symbol": "AAA", "date": "2026-07-18", "value": 12.0}]
    )
    adapter.save_cache(cached, as_of)

    result = adapter.fetch([], as_of)

    assert result.status.status == DataStatus.CACHED
    assert result.data.iloc[0]["value"] == 12.0
    assert result.data.iloc[0]["source_status"] == DataStatus.CACHED.value
    assert "provider down" in (result.status.error or "")


def test_failed_source_without_cache_is_explicitly_unavailable(tmp_path: Path) -> None:
    adapter = DummyAdapter(tmp_path)
    as_of = datetime(2026, 7, 19, tzinfo=timezone.utc)

    result = adapter.fetch([], as_of)

    assert result.status.status == DataStatus.UNAVAILABLE
    assert result.data.empty
    assert result.status.records == 0

class ExplodingAdapter(DummyAdapter):
    source_name = "exploding"

    def fetch(
        self,
        universe: list[SymbolConfig],
        as_of: datetime,
        offline: bool = False,
    ) -> AdapterResult:
        raise RuntimeError("unexpected bug")


def test_unexpected_adapter_error_is_isolated(tmp_path: Path) -> None:
    from pipeline.run_pipeline import fetch_source_safely

    adapter = ExplodingAdapter(tmp_path)
    as_of = datetime(2026, 7, 19, tzinfo=timezone.utc)
    result = fetch_source_safely(adapter, [], as_of, offline=False)

    assert result.status.status == DataStatus.UNAVAILABLE
    assert result.data.empty
    assert "unexpected adapter failure" in (result.status.error or "")
