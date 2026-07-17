from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class FixtureDashboardService:
    """Read-only deterministic dashboard adapter used by demo and tests."""

    def __init__(self, fixture_path: Path) -> None:
        self._snapshot: dict[str, Any] = json.loads(fixture_path.read_text(encoding="utf-8"))

    def snapshot(self, now: datetime | None = None) -> dict[str, Any]:
        result = deepcopy(self._snapshot)
        result["generated_at"] = (now or datetime.now(UTC)).isoformat().replace("+00:00", "Z")
        return result
