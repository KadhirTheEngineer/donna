# Donna laptop service

This component is the laptop-hosted API edge and modular monolith. The initial
slice serves health, authenticated device pairing, a deterministic dashboard
fixture, and invalidation events. It never calls Ollama or external providers.

Dependency direction is `api -> application -> domain <- adapters`. Domain code
does not import FastAPI, provider clients, or persistence models. Demo mode uses
in-memory repositories. PostgreSQL identity and durable event adapters implement
the same interfaces and are covered by an opt-in restart integration test.

## Develop

From the repository root on Windows:

    scripts\bootstrap.cmd
    scripts\check.cmd
    scripts\run-demo-server.cmd

In another laptop terminal, create a short-lived code:

    .venv\Scripts\python -m donna_server pairing-code

On the client, run `donna pair` and enter the code at the prompt. The client
generates its Ed25519 key in-process, stores the private key in the platform
credential manager, and sends only its public key to the server. The code and
private key are not placed in process arguments or configuration.

The server binds only to `127.0.0.1:8742`. Configuration rejects a non-loopback
bind in this milestone. Browse `/v1/health` for safe component health.

Important tests cover pairing expiry and one-time use, signed request replay,
dashboard authentication, contract fixtures, and WebSocket invalidation.

For a local passwordless PostgreSQL development database, set
`DONNA_DATABASE_DSN` to a loopback-only DSN and run `scripts\migrate.cmd`. The runner takes an advisory
lock, applies each migration transactionally, records its SHA-256 digest, and
refuses changed history. Do not place the DSN in command arguments or commit it.

For a loopback demo of invalidation, post to
`/v1/demo/dashboard/invalidate`. Connected clients receive the typed event and
fetch a fresh snapshot. The endpoint is unavailable outside demo mode or
outside loopback.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `DONNA_ENVIRONMENT` | `demo` | `demo`, `development`, or `production` |
| `DONNA_BIND_HOST` | `127.0.0.1` | Loopback bind; other values are rejected |
| `DONNA_BIND_PORT` | `8742` | API port |
| `DONNA_PAIRING_TTL_SECONDS` | `300` | Pairing code lifetime, 60-900 seconds |
| `DONNA_REPLAY_WINDOW_SECONDS` | `120` | Signed request clock window, 30-300 seconds |

Secrets are never accepted from environment variables, command-line arguments,
or logs. `DONNA_DATABASE_DSN` is currently development-only and must not contain
a password. Device private keys are generated and retained only by clients.

## Failure and recovery

- `pairing_code_invalid`: request a fresh code on the laptop.
- `authentication_failed`: pair again or inspect device revocation.
- `request_replayed`: retry with a new nonce and current timestamp.
- stale client data: the client preserves its last snapshot, marks it stale, and
  refreshes after reconnection or invalidation.

Demo identity state is intentionally ephemeral and is reported as degraded in
health. Production application construction refuses to start unless both durable
identity and event adapters are explicitly supplied. Host deployment wiring and
database credential resolution remain a reviewed deployment step, not an
implicit fallback to demo storage.
