-- Replace the unused credential hash placeholder with Ed25519 public keys and
-- add the durable event replay store.
ALTER TABLE identity.devices RENAME COLUMN credential_hash TO public_key;

CREATE SCHEMA IF NOT EXISTS events;

CREATE TABLE events.outbox (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id text NOT NULL UNIQUE,
    occurred_at timestamptz NOT NULL,
    event_type text NOT NULL,
    resource_id text NULL,
    trace_id text NOT NULL,
    data jsonb NOT NULL
);

CREATE INDEX outbox_occurred_at_idx ON events.outbox (occurred_at);

-- Recovery: dropping events.outbox loses retained WebSocket replay and forces
-- every client to refresh its snapshot. Renaming public_key back to
-- credential_hash is metadata-only while no released version consumes it.
