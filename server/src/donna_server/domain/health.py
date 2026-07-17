from __future__ import annotations

from typing import Any, Protocol


class HealthProbe(Protocol):
    def snapshot(self) -> list[dict[str, Any]]: ...
