from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DonnaError(Exception):
    code: str
    safe_message: str
    status_code: int
    retryable: bool = False
    fields: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.safe_message
