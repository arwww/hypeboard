from __future__ import annotations

import json
from pathlib import Path

from pipeline.models import LatestPayload, MetaPayload, SymbolHistoryPayload


def export_schemas(root: Path) -> None:
    target = root / "pipeline" / "validation" / "schemas"
    target.mkdir(parents=True, exist_ok=True)
    schemas = {
        "latest.schema.json": LatestPayload.model_json_schema(),
        "meta.schema.json": MetaPayload.model_json_schema(),
        "history.schema.json": SymbolHistoryPayload.model_json_schema(),
    }
    for name, schema in schemas.items():
        (target / name).write_text(
            json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
        )
