from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CalendarEvent:
    id: str
    source: str
    source_id: str
    calendar_id: str
    title: str
    starts_at: datetime
    ends_at: datetime
    location: str | None
    status: str
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CalendarSyncPage:
    schema_version: str
    account_id: str
    events: tuple[CalendarEvent, ...]
    next_cursor: str | None
    source_updated_at: datetime


@dataclass(frozen=True, slots=True)
class ConnectorHealth:
    state: str
    last_success: datetime | None
    last_error_category: str | None
    remediation: str | None


class CalendarConnector(Protocol):
    def health(self) -> ConnectorHealth: ...

    def sync_page(self, cursor: str | None) -> CalendarSyncPage: ...

    def fetch_by_id(self, source_id: str) -> CalendarEvent | None: ...
