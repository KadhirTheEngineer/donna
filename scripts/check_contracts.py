from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "dashboard-snapshot.v1.json": "dashboard-snapshot.v1.json",
    "event.dashboard-invalidated.v1.json": "event.v1.json",
}


def main() -> None:
    for example_name, schema_name in CASES.items():
        example = json.loads((ROOT / "contracts" / "examples" / example_name).read_text())
        schema = json.loads((ROOT / "contracts" / "schemas" / schema_name).read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)
        print(f"valid: {example_name} -> {schema_name}")


if __name__ == "__main__":
    main()
