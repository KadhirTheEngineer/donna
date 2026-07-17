# Trace the connected dashboard

This tutorial follows one read-only dashboard request from the Rust client to
the laptop service and back. It uses only sanitized demo data.

## 1. Prepare and verify

From PowerShell in the repository root:

    scripts\bootstrap.cmd
    scripts\check.cmd

The check command validates Python formatting, types, tests, contracts,
migrations, configuration, and all required Rust checks.

## 2. Start the laptop service

    scripts\run-demo-server.cmd

The entry point loads typed settings in `server/src/donna_server/config.py` and
builds the FastAPI edge in `api/app.py`. The edge owns HTTP concerns; pairing
and signature decisions live in `application/identity.py`; demo persistence and
dashboard data are replaceable adapters.

Open `http://127.0.0.1:8742/v1/health`. Degraded is expected: identity is
ephemeral and dashboard data is a fixture. Each component includes a remedy.

## 3. Pair a client

In another laptop terminal:

    .venv\Scripts\python -m donna_server pairing-code

On the client:

    donna pair

Enter the six-digit code when prompted. The code is single-use and expires. The
client generates an Ed25519 private key locally, stores it in the operating-system
credential manager, and pairs only its public key; neither code nor private key appears in
process arguments or configuration.

## 4. Enable connected mode

Run `donna config path`, create that file from `donna config example`, and set:

    [ui]
    show_demo_data = false

The client connection thread signs `GET /v1/dashboard` with device ID,
timestamp, nonce, and body hash. The API dependency authenticates it before
`FixtureDashboardService.snapshot` returns the shared contract example.

The reducer in `src/app.rs` changes visible state from CONNECTING to ONLINE.
If the server disappears, the last explicitly cacheable snapshot remains on
screen as STALE. It is never presented as current.

## 5. Observe invalidation

Post an invalidation from laptop loopback:

    Invoke-RestMethod -Method Post http://127.0.0.1:8742/v1/demo/dashboard/invalidate

`MemoryEventBus` assigns an event ID and sequence. The authenticated WebSocket
sends it, `src/connection.rs` deduplicates the sequence, and the client fetches
a fresh snapshot. Unknown event types are ignored safely.

## Replace a boundary

- Replace demo dashboard data by implementing the dashboard service interface,
  without changing authentication or the Rust reducer.
- Replace in-memory identity and events with PostgreSQL repositories, without
  changing API routes or domain records.
- Change the wire format only through `contracts/schemas`, examples, and both
  component contract tests.
