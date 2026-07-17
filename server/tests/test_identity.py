from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from donna_server.adapters.memory_identity import MemoryIdentityRepository
from donna_server.application.identity import IdentityService
from donna_server.domain.errors import DonnaError
from donna_server.domain.identity import DeviceCredential

ROOT = Path(__file__).resolve().parents[2]


def _decode_secret(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _private_key(seed: bytes = bytes(range(32))) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(seed)


def _public_key_text(key: Ed25519PrivateKey) -> str:
    raw = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _signature(key: Ed25519PrivateKey, timestamp: str, nonce: str, path: str) -> str:
    body_hash = hashlib.sha256(b"").hexdigest()
    message = f"GET\n{path}\n{timestamp}\n{nonce}\n{body_hash}".encode()
    return base64.urlsafe_b64encode(key.sign(message)).decode("ascii").rstrip("=")


def test_pairing_code_is_one_time_and_signed_requests_reject_replay() -> None:
    repository = MemoryIdentityRepository()
    service = IdentityService(repository, pairing_ttl_seconds=300, replay_window_seconds=120)
    now = datetime(2026, 7, 16, 20, tzinfo=UTC)
    key = _private_key()
    code, _ = service.create_pairing_code(now)
    issued = service.pair_device(
        code, "test device", ("dashboard.read",), _public_key_text(key), now
    )

    with pytest.raises(DonnaError, match="invalid, expired, or already used"):
        service.pair_device(code, "duplicate", (), _public_key_text(key), now)

    timestamp = now.isoformat().replace("+00:00", "Z")
    nonce = "nonce-000000000001"
    signature = _signature(key, timestamp, nonce, "/v1/dashboard")
    authenticated = service.authenticate(
        device_id=issued.device_id,
        timestamp_text=timestamp,
        nonce=nonce,
        signature=signature,
        method="GET",
        path="/v1/dashboard",
        now=now,
    )
    assert authenticated.friendly_name == "test device"

    with pytest.raises(DonnaError) as replay:
        service.authenticate(
            device_id=issued.device_id,
            timestamp_text=timestamp,
            nonce=nonce,
            signature=signature,
            method="GET",
            path="/v1/dashboard",
            now=now,
        )
    assert replay.value.code == "request_replayed"


def test_expired_pairing_code_is_rejected() -> None:
    service = IdentityService(MemoryIdentityRepository(), 60, 120)
    now = datetime(2026, 7, 16, 20, tzinfo=UTC)
    code, _ = service.create_pairing_code(now)
    with pytest.raises(DonnaError) as error:
        service.pair_device(
            code,
            "late",
            (),
            _public_key_text(_private_key()),
            now + timedelta(seconds=61),
        )
    assert error.value.code == "pairing_code_invalid"


def test_shared_cross_language_signature_fixture_authenticates() -> None:
    fixture = json.loads(
        (ROOT / "contracts/examples/auth-signature.v1.json").read_text(encoding="utf-8")
    )
    repository = MemoryIdentityRepository()
    timestamp = datetime.fromisoformat(fixture["timestamp"].replace("Z", "+00:00"))
    repository.save_device(
        DeviceCredential(
            device_id=fixture["device_id"],
            friendly_name="signature fixture",
            public_key=_decode_secret(fixture["public_key_base64url"]),
            capabilities=("dashboard.read",),
            created_at=timestamp,
        )
    )
    service = IdentityService(repository, 300, 120)
    device = service.authenticate(
        device_id=fixture["device_id"],
        timestamp_text=fixture["timestamp"],
        nonce=fixture["nonce"],
        signature=fixture["signature"],
        method=fixture["method"],
        path=fixture["path"],
        now=timestamp,
    )
    assert device.device_id == "device_fixture"
