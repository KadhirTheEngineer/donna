from __future__ import annotations

import base64
import hashlib
import os
from datetime import UTC, datetime
from uuid import uuid4

import psycopg
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from donna_server.adapters.postgres_identity import PostgresIdentityRepository
from donna_server.api.app import create_app
from donna_server.config import Settings
from donna_server.events.postgres import PostgresEventBus
from fastapi.testclient import TestClient

DSN = os.getenv("DONNA_TEST_DATABASE_DSN")
pytestmark = pytest.mark.skipif(DSN is None, reason="DONNA_TEST_DATABASE_DSN is not configured")


def _text(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _headers(device_id: str, key: Ed25519PrivateKey, path: str) -> dict[str, str]:
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    nonce = f"nonce-{uuid4().hex}"
    body_hash = hashlib.sha256(b"").hexdigest()
    message = f"GET\n{path}\n{timestamp}\n{nonce}\n{body_hash}".encode()
    return {
        "X-Donna-Device-Id": device_id,
        "X-Donna-Timestamp": timestamp,
        "X-Donna-Nonce": nonce,
        "X-Donna-Signature": _text(key.sign(message)),
    }


def test_pairing_and_event_replay_survive_application_restart() -> None:
    assert DSN is not None
    with psycopg.connect(DSN) as connection:
        connection.execute(
            "TRUNCATE identity.request_nonces, identity.devices, "
            "identity.pairing_codes, events.outbox RESTART IDENTITY"
        )

    key = Ed25519PrivateKey.generate()
    public_key = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    repository = PostgresIdentityRepository(DSN)
    first_events = PostgresEventBus(DSN)
    first_app = create_app(
        Settings(environment="production"),
        identity_repository=repository,
        event_bus=first_events,
    )
    with TestClient(first_app) as client:
        code = client.post("/v1/pairing/codes").json()["code"]
        paired = client.post(
            "/v1/pairing/complete",
            json={
                "code": code,
                "friendly_name": "restart fixture",
                "capabilities": ["dashboard.read", "events.read"],
                "public_key": _text(public_key),
            },
        )
        assert paired.status_code == 200
        device_id = paired.json()["device_id"]
        first_events.publish(
            "dashboard.invalidated",
            "dashboard:today",
            "trace-before-restart",
            {"reason": "integration_test"},
        )

    second_events = PostgresEventBus(DSN)
    restarted_app = create_app(
        Settings(environment="production"),
        identity_repository=PostgresIdentityRepository(DSN),
        event_bus=second_events,
    )
    with TestClient(restarted_app) as client:
        response = client.get(
            "/v1/dashboard?window=today",
            headers=_headers(device_id, key, "/v1/dashboard"),
        )
    assert response.status_code == 200
    replay, retained = second_events.replay_after(0)
    assert retained is True
    assert replay[0]["type"] == "dashboard.invalidated"
