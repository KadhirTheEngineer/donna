# Donna laptop service

This component is the laptop-hosted API edge and modular monolith. The initial
slice serves health, authenticated device pairing, a deterministic dashboard
fixture, and invalidation events. It never calls Ollama or external providers.

Dependency direction is `api -> application -> domain <- adapters`. Domain code
does not import FastAPI, provider clients, or persistence models. Demo mode uses
in-memory repositories; production persistence will implement the same domain
interfaces with PostgreSQL and checked-in migrations.

## Develop

From the repository root on Windows:

    scripts\bootstrap.cmd
    scripts\check.cmd
    scripts\run-demo-server.cmd

In another laptop terminal, create a short-lived code:

    .venv\Scripts\python -m donna_server pairing-code

On the client, run `donna pair` and enter the code at the prompt. The code is
not placed in process arguments and the issued credential is stored in the
platform credential manager.

The server binds only to `127.0.0.1:8742`. Configuration rejects a non-loopback
bind in this milestone. Browse `/v1/health` for safe component health.

Important tests cover pairing expiry and one-time use, signed request replay,
dashboard authentication, contract fixtures, and WebSocket invalidation.

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
or logs. Pairing credentials are returned once over the pairing exchange.

## Failure and recovery

- `pairing_code_invalid`: request a fresh code on the laptop.
- `authentication_failed`: pair again or inspect device revocation.
- `request_replayed`: retry with a new nonce and current timestamp.
- stale client data: the client preserves its last snapshot, marks it stale, and
  refreshes after reconnection or invalidation.

Demo identity state is intentionally ephemeral and is reported as degraded in
health. Production mode will not claim ready until durable identity and event
repositories are configured.
