from __future__ import annotations

import asyncio
from collections import deque
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4


class MemoryEventBus:
    def __init__(self, retention: int = 256) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=retention)
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._sequence = 0
        self._lock = Lock()

    def publish(
        self,
        event_type: str,
        resource_id: str | None,
        trace_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        with self._lock:
            self._sequence += 1
            event = {
                "schema_version": "1.0",
                "event_id": f"event_{uuid4().hex}",
                "sequence": self._sequence,
                "occurred_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "type": event_type,
                "resource_id": resource_id,
                "trace_id": trace_id,
                "data": data,
            }
            self._events.append(event)
            subscribers = tuple(self._subscribers)
        for subscriber in subscribers:
            subscriber.put_nowait(event)
        return event

    def replay_after(self, sequence: int) -> tuple[list[dict[str, Any]], bool]:
        with self._lock:
            if self._events and sequence < self._events[0]["sequence"] - 1:
                return [], False
            return [event for event in self._events if event["sequence"] > sequence], True

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=64)
        with self._lock:
            self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        with self._lock:
            self._subscribers.discard(queue)
