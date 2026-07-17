from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PairingCode:
    digest: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class DeviceCredential:
    device_id: str
    friendly_name: str
    secret: bytes
    capabilities: tuple[str, ...]
    created_at: datetime
    revoked_at: datetime | None = None


class IdentityRepository(Protocol):
    def save_pairing_code(self, code: PairingCode) -> None: ...

    def consume_pairing_code(self, digest: str, now: datetime) -> bool: ...

    def save_device(self, credential: DeviceCredential) -> None: ...

    def get_device(self, device_id: str) -> DeviceCredential | None: ...

    def claim_nonce(
        self, device_id: str, nonce: str, now: datetime, expires_at: datetime
    ) -> bool: ...
