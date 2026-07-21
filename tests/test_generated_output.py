import json

import jsonschema
from pathlib import Path

from pipeline.models import LatestPayload, MetaPayload, SymbolHistoryPayload
from pipeline.validation.validate_output import validate_output


ROOT = Path(__file__).resolve().parents[1]


def test_generated_json_matches_pydantic_schema() -> None:
    data = ROOT / "frontend" / "public" / "data"
    latest = LatestPayload.model_validate_json((data / "latest.json").read_text())
    meta = MetaPayload.model_validate_json((data / "meta.json").read_text())
    nvda = SymbolHistoryPayload.model_validate_json(
        (data / "history" / "NVDA.json").read_text()
    )
    assert len(latest.symbols) == meta.universe_size == 30
    assert nvda.symbol == "NVDA"


def test_generated_history_has_no_duplicate_trading_days() -> None:
    history_dir = ROOT / "frontend" / "public" / "data" / "history"
    for path in history_dir.glob("*.json"):
        history = SymbolHistoryPayload.model_validate_json(path.read_text())
        dates = [point.date for point in history.points]
        assert len(dates) == len(set(dates))


def test_full_data_quality_validation() -> None:
    warnings = validate_output(ROOT)
    assert isinstance(warnings, list)


def test_generated_json_matches_exported_json_schemas() -> None:
    data_dir = ROOT / "frontend" / "public" / "data"
    schema_dir = ROOT / "pipeline" / "validation" / "schemas"
    cases = [
        (data_dir / "latest.json", schema_dir / "latest.schema.json"),
        (data_dir / "meta.json", schema_dir / "meta.schema.json"),
        (data_dir / "history" / "NVDA.json", schema_dir / "history.schema.json"),
    ]
    for payload_path, schema_path in cases:
        jsonschema.validate(
            instance=json.loads(payload_path.read_text()),
            schema=json.loads(schema_path.read_text()),
        )
