from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol


class DashboardService(Protocol):
    def snapshot(self, now: datetime | None = None) -> dict[str, Any]: ...
