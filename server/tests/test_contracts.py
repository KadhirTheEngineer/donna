from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]


def test_dashboard_example_matches_schema() -> None:
    schema = json.loads(
        (ROOT / "contracts/schemas/dashboard-snapshot.v1.json").read_text(encoding="utf-8")
    )
    example = json.loads(
        (ROOT / "contracts/examples/dashboard-snapshot.v1.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)


def test_event_example_matches_schema() -> None:
    schema = json.loads((ROOT / "contracts/schemas/event.v1.json").read_text(encoding="utf-8"))
    example = json.loads(
        (ROOT / "contracts/examples/event.dashboard-invalidated.v1.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)
