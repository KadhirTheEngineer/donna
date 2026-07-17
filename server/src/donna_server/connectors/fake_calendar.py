from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from donna_server.domain.calendar import (
    CalendarEvent,
    CalendarSyncPage,
    ConnectorHealth,
)


class FakeCalendarConnector:
    """Deterministic Google-shaped calendar behavior without provider access."""

    def __init__(self, fixture_path: Path) -> None:
        raw = json.loads(fixture_path.read_text(encoding="utf-8"))
        self._page = CalendarSyncPage(
            schema_version=raw["schema_version"],
            account_id=raw["account_id"],
            events=tuple(self._event(item) for item in raw["events"]),
            next_cursor=raw["next_cursor"],
            source_updated_at=self._timestamp(raw["source_updated_at"]),
        )

    def health(self) -> ConnectorHealth:
        return ConnectorHealth(
            state="degraded",
            last_success=self._page.source_updated_at,
            last_error_category="fake_adapter",
            remediation="Complete the approved Google OAuth design before provider enrollment.",
        )

    def sync_page(self, cursor: str | None) -> CalendarSyncPage:
        if cursor not in {None, "fixture-cursor-1"}:
            return CalendarSyncPage(
                schema_version="1.0",
                account_id=self._page.account_id,
                events=(),
                next_cursor=None,
                source_updated_at=self._page.source_updated_at,
            )
        return self._page

    def fetch_by_id(self, source_id: str) -> CalendarEvent | None:
        return next((event for event in self._page.events if event.source_id == source_id), None)

    @classmethod
    def _event(cls, raw: dict[str, object]) -> CalendarEvent:
        return CalendarEvent(
            id=str(raw["id"]),
            source=str(raw["source"]),
            source_id=str(raw["source_id"]),
            calendar_id=str(raw["calendar_id"]),
            title=str(raw["title"]),
            starts_at=cls._timestamp(str(raw["starts_at"])),
            ends_at=cls._timestamp(str(raw["ends_at"])),
            location=str(raw["location"]) if raw["location"] is not None else None,
            status=str(raw["status"]),
            updated_at=cls._timestamp(str(raw["updated_at"])),
        )

    @staticmethod
    def _timestamp(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(UTC)
