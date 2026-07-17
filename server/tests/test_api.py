from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from donna_server.api.app import create_app
from donna_server.config import Settings
from fastapi.testclient import TestClient


def _headers(device_id: str, private_key_text: str, path: str) -> dict[str, str]:
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    nonce = f"nonce-{uuid4().hex}"
    seed = base64.urlsafe_b64decode(private_key_text + "=" * (-len(private_key_text) % 4))
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    body_hash = hashlib.sha256(b"").hexdigest()
    message = f"GET\n{path}\n{timestamp}\n{nonce}\n{body_hash}".encode()
    signature = base64.urlsafe_b64encode(private_key.sign(message)).decode().rstrip("=")
    return {
        "X-Donna-Device-Id": device_id,
        "X-Donna-Timestamp": timestamp,
        "X-Donna-Nonce": nonce,
        "X-Donna-Signature": signature,
    }


def _pair(client: TestClient) -> tuple[str, str]:
    private_key = Ed25519PrivateKey.generate()
    private_seed = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    code_response = client.post("/v1/pairing/codes")
    assert code_response.status_code == 200
    paired = client.post(
        "/v1/pairing/complete",
        json={
            "code": code_response.json()["code"],
            "friendly_name": "contract test",
            "capabilities": ["dashboard.read", "events.read"],
            "public_key": base64.urlsafe_b64encode(public_key).decode().rstrip("="),
        },
    )
    assert paired.status_code == 200
    return paired.json()["device_id"], base64.urlsafe_b64encode(private_seed).decode().rstrip("=")


def test_health_explains_demo_degradation() -> None:
    with TestClient(create_app(Settings())) as client:
        response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert {item["component"] for item in response.json()["components"]} >= {
        "api",
        "identity_store",
        "dashboard",
        "storage",
        "gpu",
        "ollama",
    }
    assert response.headers["X-Donna-Request-Id"].startswith("request_")


def test_dashboard_requires_authentication_and_returns_contract_fixture() -> None:
    with TestClient(create_app(Settings())) as client:
        unauthorized = client.get("/v1/dashboard")
        assert unauthorized.status_code == 401
        assert unauthorized.json()["code"] == "authentication_failed"
        device_id, secret = _pair(client)
        response = client.get(
            "/v1/dashboard?window=today",
            headers=_headers(device_id, secret, "/v1/dashboard"),
        )
    assert response.status_code == 200
    assert response.json()["schema_version"] == "1.0"
    assert response.json()["freshness"]["state"] == "current"


def test_websocket_replays_dashboard_invalidation() -> None:
    app = create_app(Settings())
    with TestClient(app) as client:
        device_id, secret = _pair(client)
        app.state.events.publish(
            "dashboard.invalidated",
            "dashboard:today",
            "trace-contract-test",
            {"reason": "fixture_changed"},
        )
        with client.websocket_connect(
            "/v1/events?after=0",
            headers=_headers(device_id, secret, "/v1/events"),
        ) as websocket:
            event = websocket.receive_json()
    assert event["type"] == "dashboard.invalidated"
    assert event["sequence"] == 1


def test_demo_invalidation_endpoint_emits_typed_event() -> None:
    with TestClient(create_app(Settings())) as client:
        response = client.post("/v1/demo/dashboard/invalidate")
    assert response.status_code == 200
    assert response.json()["type"] == "dashboard.invalidated"
    assert response.json()["resource_id"] == "dashboard:today"
