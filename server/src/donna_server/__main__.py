from __future__ import annotations

import json
import sys
import urllib.request

import uvicorn

from donna_server.adapters.local_health import LocalHealthProbe
from donna_server.api.app import create_app
from donna_server.config import Settings


def main() -> None:
    settings = Settings.from_environment()
    if sys.argv[1:] == ["validate-config"]:
        settings.validate()
        print("Donna server configuration is valid (secrets omitted).")
        return
    if sys.argv[1:] == ["pairing-code"]:
        request = urllib.request.Request(
            f"http://{settings.bind_host}:{settings.bind_port}/v1/pairing/codes",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.load(response)
        print(f"Pairing code: {result['code']}")
        print(f"Expires at: {result['expires_at']}")
        return
    if sys.argv[1:]:
        raise SystemExit("usage: donna-server [pairing-code|validate-config]")
    uvicorn.run(
        create_app(settings, health_probe=LocalHealthProbe()),
        host=settings.bind_host,
        port=settings.bind_port,
    )


if __name__ == "__main__":
    main()
