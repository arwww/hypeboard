from __future__ import annotations

import json
from pathlib import Path

from pipeline.models import LatestPayload, MetaPayload, SymbolHistoryPayload
from pipeline.validation.data_quality import validate_payloads


def validate_output(root: Path) -> list[str]:
    public_data = root / "frontend" / "public" / "data"
    latest = LatestPayload.model_validate_json((public_data / "latest.json").read_text())
    meta = MetaPayload.model_validate_json((public_data / "meta.json").read_text())
    universe = json.loads((root / "pipeline" / "config" / "universe.json").read_text())
    histories = [
        SymbolHistoryPayload.model_validate_json(path.read_text())
        for path in sorted((public_data / "history").glob("*.json"))
    ]
    return validate_payloads(
        latest, meta, histories, expected_universe_size=sum(1 for item in universe if item["active"])
    )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    warnings = validate_output(root)
    if warnings:
        print("Validation completed with warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("Validation completed without warnings.")


if __name__ == "__main__":
    main()
