from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb


class PostgresEventBus:
    """Durable replay with in-process live fanout for the modular monolith."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._lock = Lock()

    def publish(
        self,
        event_type: str,
        resource_id: str | None,
        trace_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        event_id = f"event_{uuid4().hex}"
        occurred_at = datetime.now(UTC)
        with psycopg.connect(self._dsn) as connection:
            row = connection.execute(
                """
                INSERT INTO events.outbox (
                    event_id, occurred_at, event_type, resource_id, trace_id, data
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING sequence
                """,
                (event_id, occurred_at, event_type, resource_id, trace_id, Jsonb(data)),
            ).fetchone()
        if row is None:
            raise RuntimeError("PostgreSQL did not return the committed event sequence")
        event = {
            "schema_version": "1.0",
            "event_id": event_id,
            "sequence": row[0],
            "occurred_at": occurred_at.isoformat().replace("+00:00", "Z"),
            "type": event_type,
            "resource_id": resource_id,
            "trace_id": trace_id,
            "data": data,
        }
        with self._lock:
            subscribers = tuple(self._subscribers)
        for subscriber in subscribers:
            try:
                subscriber.put_nowait(event)
            except asyncio.QueueFull:
                self.unsubscribe(subscriber)
        return event

    def replay_after(self, sequence: int) -> tuple[list[dict[str, Any]], bool]:
        with psycopg.connect(self._dsn) as connection:
            minimum = connection.execute("SELECT min(sequence) FROM events.outbox").fetchone()
            rows = connection.execute(
                """
                SELECT sequence, event_id, occurred_at, event_type, resource_id, trace_id, data
                FROM events.outbox
                WHERE sequence > %s
                ORDER BY sequence
                """,
                (sequence,),
            ).fetchall()
        minimum_sequence = minimum[0] if minimum else None
        retained = minimum_sequence is None or sequence >= minimum_sequence - 1
        events = [
            {
                "schema_version": "1.0",
                "event_id": row[1],
                "sequence": row[0],
                "occurred_at": row[2].isoformat().replace("+00:00", "Z"),
                "type": row[3],
                "resource_id": row[4],
                "trace_id": row[5],
                "data": row[6],
            }
            for row in rows
        ]
        return events, retained

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=64)
        with self._lock:
            self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        with self._lock:
            self._subscribers.discard(queue)
