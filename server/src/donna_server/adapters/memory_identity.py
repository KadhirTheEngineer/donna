from __future__ import annotations

from datetime import datetime
from threading import Lock

from donna_server.domain.identity import DeviceCredential, PairingCode


class MemoryIdentityRepository:
    """Thread-safe ephemeral identity storage for deterministic demo mode."""

    def __init__(self) -> None:
        self._pairing_codes: dict[str, PairingCode] = {}
        self._devices: dict[str, DeviceCredential] = {}
        self._nonces: dict[tuple[str, str], datetime] = {}
        self._lock = Lock()

    def save_pairing_code(self, code: PairingCode) -> None:
        with self._lock:
            self._pairing_codes[code.digest] = code

    def consume_pairing_code(self, digest: str, now: datetime) -> bool:
        with self._lock:
            code = self._pairing_codes.pop(digest, None)
            return code is not None and code.expires_at >= now

    def save_device(self, credential: DeviceCredential) -> None:
        with self._lock:
            self._devices[credential.device_id] = credential

    def get_device(self, device_id: str) -> DeviceCredential | None:
        with self._lock:
            return self._devices.get(device_id)

    def claim_nonce(self, device_id: str, nonce: str, now: datetime, expires_at: datetime) -> bool:
        with self._lock:
            self._nonces = {key: expiry for key, expiry in self._nonces.items() if expiry >= now}
            key = (device_id, nonce)
            if key in self._nonces:
                return False
            self._nonces[key] = expires_at
            return True
