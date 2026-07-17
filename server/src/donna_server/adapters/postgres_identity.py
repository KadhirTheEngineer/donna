from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from donna_server.domain.identity import DeviceCredential, PairingCode


class PostgresIdentityRepository:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def save_pairing_code(self, code: PairingCode) -> None:
        with psycopg.connect(self._dsn) as connection:
            connection.execute(
                """
                INSERT INTO identity.pairing_codes (code_hash, expires_at)
                VALUES (%s, %s)
                ON CONFLICT (code_hash) DO UPDATE
                SET expires_at = EXCLUDED.expires_at, consumed_at = NULL
                """,
                (bytes.fromhex(code.digest), code.expires_at),
            )

    def consume_pairing_code(self, digest: str, now: datetime) -> bool:
        with psycopg.connect(self._dsn) as connection:
            cursor = connection.execute(
                """
                UPDATE identity.pairing_codes
                SET consumed_at = %s
                WHERE code_hash = %s
                  AND consumed_at IS NULL
                  AND expires_at >= %s
                RETURNING code_hash
                """,
                (now, bytes.fromhex(digest), now),
            )
            return cursor.fetchone() is not None

    def save_device(self, credential: DeviceCredential) -> None:
        with psycopg.connect(self._dsn) as connection:
            connection.execute(
                """
                INSERT INTO identity.devices (
                    device_id, friendly_name, public_key, capabilities, created_at, revoked_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    credential.device_id,
                    credential.friendly_name,
                    credential.public_key,
                    Jsonb(list(credential.capabilities)),
                    credential.created_at,
                    credential.revoked_at,
                ),
            )

    def get_device(self, device_id: str) -> DeviceCredential | None:
        with psycopg.connect(self._dsn) as connection:
            row = connection.execute(
                """
                SELECT device_id, friendly_name, public_key, capabilities, created_at, revoked_at
                FROM identity.devices
                WHERE device_id = %s
                """,
                (device_id,),
            ).fetchone()
            if row is None:
                return None
            capabilities: list[Any] = row[3]
            return DeviceCredential(
                device_id=row[0],
                friendly_name=row[1],
                public_key=bytes(row[2]),
                capabilities=tuple(str(value) for value in capabilities),
                created_at=row[4],
                revoked_at=row[5],
            )

    def claim_nonce(self, device_id: str, nonce: str, now: datetime, expires_at: datetime) -> bool:
        nonce_hash = hashlib.sha256(nonce.encode()).digest()
        with psycopg.connect(self._dsn) as connection:
            connection.execute("DELETE FROM identity.request_nonces WHERE expires_at < %s", (now,))
            cursor = connection.execute(
                """
                INSERT INTO identity.request_nonces (device_id, nonce_hash, expires_at)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING nonce_hash
                """,
                (device_id, nonce_hash, expires_at),
            )
            return cursor.fetchone() is not None
