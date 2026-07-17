-- Donna identity foundation. Apply inside a transaction with the migration runner.
CREATE SCHEMA IF NOT EXISTS identity;

CREATE TABLE identity.devices (
    device_id text PRIMARY KEY,
    friendly_name text NOT NULL,
    credential_hash bytea NOT NULL,
    capabilities jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL,
    revoked_at timestamptz NULL,
    last_seen_at timestamptz NULL
);

CREATE TABLE identity.pairing_codes (
    code_hash bytea PRIMARY KEY,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE identity.request_nonces (
    device_id text NOT NULL REFERENCES identity.devices(device_id),
    nonce_hash bytea NOT NULL,
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (device_id, nonce_hash)
);

CREATE INDEX request_nonces_expiry_idx ON identity.request_nonces (expires_at);

-- Recovery: before production data exists this migration can be reversed with
-- DROP SCHEMA identity CASCADE. After enrollment begins, restore from backup or
-- migrate device records; dropping identity would revoke every paired device.
