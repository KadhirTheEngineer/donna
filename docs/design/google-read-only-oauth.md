# Proposed read-only Google OAuth design

Status: review required before implementation or enrollment

This design is the gate for the final connector item in the Windows handoff. No
Google project, OAuth consent screen, account enrollment, token, or API mutation
has been created by the implementation session.

Owner direction recorded 2026-07-17: read operations should be usable without
per-operation approval, while all Google writes must remain blocked until an
explicit approval is made in the CLI. Local caching of normalized Google data is
permitted; the server still declares cache policy so especially sensitive views
can be memory-only later. This direction does not constitute final approval to
begin OAuth enrollment.

## Boundary

- OAuth occurs only on the gaming laptop through the FastAPI connector adapter.
- The Rust client receives normalized Donna records, never Google tokens or SDK
  objects.
- Start with read-only Calendar only. The owner may enroll the primary account
  after reviewing this design; Gmail and Tasks remain disabled until Calendar
  sync, revocation, and retention behavior are proven.
- Request the narrowest verified read-only scope. Exact provider scope names and
  redirect requirements were last checked against official Google documentation
  on 2026-07-17. The proposed initial scopes are
  `calendar.calendarlist.readonly` to enumerate subscribed calendars and
  `calendar.events.readonly` to synchronize their events. The latter permits
  viewing events on every calendar the account can access; OAuth cannot restrict
  it to one synthetic test calendar.

## Flow

1. An owner-only laptop action creates an authorization attempt with a random
   state value, PKCE verifier, expiry, and trace ID.
2. The system browser opens Google's authorization page. Donna listens only on
   a short-lived loopback callback and verifies state and PKCE.
3. The Google adapter exchanges the code. Provider objects do not leave the
   adapter.
4. The refresh token is encrypted with Windows user-scoped credential protection.
   PostgreSQL stores only account metadata, health, cursor, and credential
   reference.
5. Calendar synchronization uses stable external IDs, incremental cursors,
   bounded pages, reconciliation, and a sanitized fake fixture for ordinary
   tests.

Google documents the loopback redirect as supported for a Windows Desktop app.
Donna binds a random available `127.0.0.1` port only for the authorization
response, uses PKCE and a one-time state value, and closes the listener after a
success, denial, mismatch, or short timeout.

## Proposed primary-account test

The first real test remains read-only even if the owner chooses the primary
Google account:

1. Create a secondary calendar named for Donna testing and add synthetic past,
   current, recurring, all-day, changed, and cancelled events in Google Calendar.
2. Before consent, show the exact requested scopes and confirm that no write
   scope is present.
3. Complete the system-browser flow and verify that Donna stores no token in
   PostgreSQL, logs, the Rust client, or committed configuration.
4. Run an initial bounded synchronization and verify the synthetic events,
   pagination, time zones, recurrence, provenance, and dashboard presentation.
5. Confirm that ordinary account events can be read because the granted scope is
   account-wide, but do not include their content in fixtures, logs, screenshots,
   or test assertions.
6. Change and cancel synthetic events in Google Calendar, run incremental sync,
   restart Donna, and verify cursor persistence and reconciliation.
7. Disconnect Donna, revoke the Google grant, delete the local normalized data,
   and verify that health reports authentication recovery without retry loops.

No Calendar write endpoint or write scope is implemented during this test. A
later mutation milestone must prove CLI preview, effect hashing, explicit
approval, idempotency, and reconciliation using synthetic events before it can
touch a real event.

## Failure and recovery

- Denied consent: mark connector disabled; do not retry automatically.
- Expired or revoked token: mark `authentication` health degradation and require
  explicit re-enrollment.
- Invalid cursor: perform a bounded full resync without deleting the last good
  local view until replacement commits.
- Rate limit or network failure: preserve cursor, categorize the error, and use
  capped backoff.
- Account mismatch: stop before importing data and show the selected account.

## Review decisions

- approve the Google project and account selected for initial enrollment;
- approve exact read-only Calendar scopes and retention policy;
- approve the loopback browser flow and Windows credential protection approach;
- confirm any exceptions to the owner-approved local caching policy;
- verify deletion/export behavior before any personal history is retained.

Implementation begins only after those decisions are reviewed. The fake Calendar
adapter and sanitized fixtures can be built independently without enrollment.
