from __future__ import annotations

from pathlib import Path

from donna_server.connectors.fake_calendar import FakeCalendarConnector

ROOT = Path(__file__).resolve().parents[2]


def connector() -> FakeCalendarConnector:
    return FakeCalendarConnector(ROOT / "contracts" / "examples" / "calendar-sync-page.v1.json")


def test_fake_calendar_sync_is_cursor_bounded_and_deterministic() -> None:
    first = connector().sync_page(None)
    assert first.events[0].source == "google_calendar"
    assert first.next_cursor == "fixture-cursor-2"

    exhausted = connector().sync_page(first.next_cursor)
    assert exhausted.events == ()
    assert exhausted.next_cursor is None


def test_fake_calendar_fetch_and_health_explain_provider_gate() -> None:
    calendar = connector()
    assert calendar.fetch_by_id("provider-event-1") is not None
    assert calendar.fetch_by_id("missing") is None
    health = calendar.health()
    assert health.state == "degraded"
    assert health.last_error_category == "fake_adapter"
    assert health.remediation is not None and "OAuth" in health.remediation
