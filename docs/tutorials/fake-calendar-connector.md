# Add and inspect a fake Calendar provider

The fake Calendar adapter lets you change connector behavior without Google
credentials, internet access, or personal data.

## Trace the boundary

1. `contracts/schemas/calendar-sync-page.v1.json` owns the cross-component
   record and cursor shape.
2. `contracts/examples/calendar-sync-page.v1.json` is the sanitized replay
   fixture used in ordinary development.
3. `server/src/donna_server/domain/calendar.py` defines provider-independent
   records and the `CalendarConnector` interface.
4. `server/src/donna_server/connectors/fake_calendar.py` is one implementation.
   Provider SDK objects are not permitted to cross this package boundary.
5. `server/tests/test_fake_calendar.py` proves deterministic cursor exhaustion,
   fetch-by-ID behavior, and visible degraded health.

Run `scripts\check.cmd` after changing the fixture or adapter. The contract
example and fake tests must change together.

## Replace it after OAuth review

Create a real Google implementation of `CalendarConnector`. Keep OAuth tokens,
Google request/response objects, pagination tokens, and provider errors inside
the adapter. Map them to `CalendarSyncPage`, `CalendarEvent`, and stable error
categories before returning.

The application service and dashboard must select the connector through typed
configuration. Do not add Google conditionals to API routes or client code. The
same contract tests should run against the fake, while dedicated integration
tests use only the approved test account.

## Failure exercise

Change the fake cursor to an unknown value and observe an empty terminal page
with no new cursor. Change health to an authentication failure and provide a
specific re-enrollment remedy. Never erase the last committed calendar view
because one incremental page failed.
