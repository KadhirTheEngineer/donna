from __future__ import annotations

import asyncio
from typing import Any, Protocol


class EventBus(Protocol):
    def publish(
        self,
        event_type: str,
        resource_id: str | None,
        trace_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]: ...

    def replay_after(self, sequence: int) -> tuple[list[dict[str, Any]], bool]: ...

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]: ...

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None: ...
