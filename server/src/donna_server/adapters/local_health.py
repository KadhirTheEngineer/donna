from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _component(
    name: str,
    state: str,
    *,
    details: dict[str, Any],
    error: str | None = None,
    remediation: str | None = None,
) -> dict[str, Any]:
    return {
        "component": name,
        "state": state,
        "last_success": _now() if state == "healthy" else None,
        "last_error_category": error,
        "dependencies": [],
        "remediation": remediation,
        "details": details,
    }


class LocalHealthProbe:
    """Sanitized, bounded host probes owned by the laptop adapter."""

    def __init__(self, volume: Path | None = None) -> None:
        self._volume = volume or Path.cwd()

    def snapshot(self) -> list[dict[str, Any]]:
        return [self._storage(), self._gpu(), self._ollama()]

    def _storage(self) -> dict[str, Any]:
        usage = shutil.disk_usage(self._volume)
        free_gib = round(usage.free / (1024**3), 1)
        state = "healthy" if free_gib >= 100 else "degraded"
        return _component(
            "storage",
            state,
            details={"free_gib": free_gib, "minimum_free_gib": 100},
            error=None if state == "healthy" else "disk_space_low",
            remediation=None if state == "healthy" else "Free space before storing artifacts.",
        )

    def _gpu(self) -> dict[str, Any]:
        try:
            process = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,driver_version,memory.total,memory.used,memory.free",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                check=True,
                text=True,
                timeout=3,
            )
            name, driver, total, used, free = [part.strip() for part in process.stdout.split(",")]
            return _component(
                "gpu",
                "healthy",
                details={
                    "name": name,
                    "driver": driver,
                    "memory_total_mib": int(total),
                    "memory_used_mib": int(used),
                    "memory_free_mib": int(free),
                },
            )
        except (FileNotFoundError, subprocess.SubprocessError, ValueError) as error:
            return _component(
                "gpu",
                "degraded",
                details={},
                error="gpu_probe_unavailable",
                remediation=(
                    f"Run nvidia-smi locally and inspect the GPU driver ({type(error).__name__})."
                ),
            )

    def _ollama(self) -> dict[str, Any]:
        try:
            version = self._ollama_get("/api/version")
            tags = self._ollama_get("/api/tags")
            loaded = self._ollama_get("/api/ps")
            models = [
                {
                    "name": model["name"],
                    "digest_prefix": model["digest"][:12],
                    "size_gib": round(model["size"] / (1024**3), 2),
                }
                for model in tags.get("models", [])
            ]
            return _component(
                "ollama",
                "healthy" if models else "degraded",
                details={
                    "version": version.get("version"),
                    "installed_models": models,
                    "loaded_model_count": len(loaded.get("models", [])),
                },
                error=None if models else "model_missing",
                remediation=None
                if models
                else "Install model roles explicitly; Donna will not pull them.",
            )
        except (
            OSError,
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
        ) as error:
            return _component(
                "ollama",
                "degraded",
                details={"endpoint": "loopback"},
                error="provider_unavailable",
                remediation=f"Confirm Ollama is running on loopback ({type(error).__name__}).",
            )

    @staticmethod
    def _ollama_get(path: str) -> dict[str, Any]:
        with urllib.request.urlopen(f"http://127.0.0.1:11434{path}", timeout=2) as response:
            result: dict[str, Any] = json.load(response)
            return result


class FakeHealthProbe:
    def snapshot(self) -> list[dict[str, Any]]:
        return [
            _component(
                "storage",
                "healthy",
                details={"free_gib": 500.0, "minimum_free_gib": 100},
            ),
            _component(
                "gpu",
                "degraded",
                details={},
                error="fake_adapter",
                remediation="Use the local probe for machine-local health.",
            ),
            _component(
                "ollama",
                "degraded",
                details={"endpoint": "fake"},
                error="fake_adapter",
                remediation="Use the local probe for machine-local health.",
            ),
        ]
