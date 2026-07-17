from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from donna_server.domain.errors import DonnaError
from donna_server.domain.identity import DeviceCredential, IdentityRepository, PairingCode


def _digest_code(code: str) -> str:
    return hashlib.sha256(code.encode("ascii")).hexdigest()


def _decode_base64url(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@dataclass(frozen=True, slots=True)
class IssuedDevice:
    device_id: str
    issued_at: datetime


class IdentityService:
    def __init__(
        self,
        repository: IdentityRepository,
        pairing_ttl_seconds: int,
        replay_window_seconds: int,
    ) -> None:
        self._repository = repository
        self._pairing_ttl = timedelta(seconds=pairing_ttl_seconds)
        self._replay_window = timedelta(seconds=replay_window_seconds)

    def create_pairing_code(self, now: datetime | None = None) -> tuple[str, datetime]:
        issued_at = now or datetime.now(UTC)
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = issued_at + self._pairing_ttl
        self._repository.save_pairing_code(PairingCode(_digest_code(code), expires_at))
        return code, expires_at

    def pair_device(
        self,
        code: str,
        friendly_name: str,
        capabilities: tuple[str, ...],
        public_key_text: str,
        now: datetime | None = None,
    ) -> IssuedDevice:
        issued_at = now or datetime.now(UTC)
        if len(code) != 6 or not code.isascii() or not code.isdigit():
            self._invalid_code()
        if not self._repository.consume_pairing_code(_digest_code(code), issued_at):
            self._invalid_code()
        try:
            public_key = _decode_base64url(public_key_text)
            Ed25519PublicKey.from_public_bytes(public_key)
        except (ValueError, TypeError):
            raise DonnaError(
                "device_key_invalid",
                "The device public key is not a valid Ed25519 key.",
                400,
            ) from None
        device_id = f"device_{secrets.token_hex(12)}"
        self._repository.save_device(
            DeviceCredential(
                device_id=device_id,
                friendly_name=friendly_name,
                public_key=public_key,
                capabilities=capabilities,
                created_at=issued_at,
            )
        )
        return IssuedDevice(device_id, issued_at)

    def authenticate(
        self,
        *,
        device_id: str,
        timestamp_text: str,
        nonce: str,
        signature: str,
        method: str,
        path: str,
        body: bytes = b"",
        now: datetime | None = None,
    ) -> DeviceCredential:
        current = now or datetime.now(UTC)
        device = self._repository.get_device(device_id)
        if device is None:
            raise DonnaError(
                "authentication_failed",
                "Device authentication failed. Pair this device again if the problem continues.",
                401,
            )
        if device.revoked_at is not None:
            self._authentication_failed()
        try:
            timestamp = datetime.fromisoformat(timestamp_text.replace("Z", "+00:00"))
        except ValueError:
            self._authentication_failed()
        if timestamp.tzinfo is None or abs(current - timestamp) > self._replay_window:
            self._authentication_failed()
        body_digest = hashlib.sha256(body).hexdigest()
        message = f"{method.upper()}\n{path}\n{timestamp_text}\n{nonce}\n{body_digest}".encode()
        try:
            signature_bytes = _decode_base64url(signature)
            Ed25519PublicKey.from_public_bytes(device.public_key).verify(signature_bytes, message)
        except (ValueError, InvalidSignature):
            self._authentication_failed()
        if not self._repository.claim_nonce(
            device_id, nonce, current, current + self._replay_window
        ):
            raise DonnaError("request_replayed", "This signed request was already used.", 409)
        return device

    @staticmethod
    def _invalid_code() -> None:
        raise DonnaError(
            "pairing_code_invalid",
            "The pairing code is invalid, expired, or already used.",
            400,
        )

    @staticmethod
    def _authentication_failed() -> None:
        raise DonnaError(
            "authentication_failed",
            "Device authentication failed. Pair this device again if the problem continues.",
            401,
        )
