from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from donna_server.domain.errors import DonnaError
from donna_server.domain.identity import DeviceCredential, IdentityRepository, PairingCode


def _digest_code(code: str) -> str:
    return hashlib.sha256(code.encode("ascii")).hexdigest()


def _secret_text(secret: bytes) -> str:
    return base64.urlsafe_b64encode(secret).decode("ascii").rstrip("=")


@dataclass(frozen=True, slots=True)
class IssuedCredential:
    device_id: str
    secret: str
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
        now: datetime | None = None,
    ) -> IssuedCredential:
        issued_at = now or datetime.now(UTC)
        if len(code) != 6 or not code.isascii() or not code.isdigit():
            self._invalid_code()
        if not self._repository.consume_pairing_code(_digest_code(code), issued_at):
            self._invalid_code()
        device_id = f"device_{secrets.token_hex(12)}"
        secret = secrets.token_bytes(32)
        self._repository.save_device(
            DeviceCredential(
                device_id=device_id,
                friendly_name=friendly_name,
                secret=secret,
                capabilities=capabilities,
                created_at=issued_at,
            )
        )
        return IssuedCredential(device_id, _secret_text(secret), issued_at)

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
        expected = hmac.new(device.secret, message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
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
