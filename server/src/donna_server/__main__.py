from __future__ import annotations

import json
import sys
import urllib.request

import psycopg
import uvicorn

from donna_server.adapters.local_health import LocalHealthProbe
from donna_server.adapters.postgres_identity import PostgresIdentityRepository
from donna_server.api.app import create_app
from donna_server.config import Settings
from donna_server.events.postgres import PostgresEventBus


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
    identity_repository = None
    event_bus = None
    if settings.database_dsn:
        try:
            with psycopg.connect(settings.database_dsn, connect_timeout=3) as connection:
                row = connection.execute(
                    "SELECT to_regclass('identity.devices'), to_regclass('events.outbox')"
                ).fetchone()
                if row is None or None in row:
                    raise SystemExit(
                        "PostgreSQL migrations are incomplete; run scripts\\migrate.cmd."
                    )
        except psycopg.Error as error:
            raise SystemExit(
                "PostgreSQL is unavailable; verify the loopback database and migrations "
                f"({type(error).__name__})."
            ) from None
        identity_repository = PostgresIdentityRepository(settings.database_dsn)
        event_bus = PostgresEventBus(settings.database_dsn)
    uvicorn.run(
        create_app(
            settings,
            health_probe=LocalHealthProbe(),
            identity_repository=identity_repository,
            event_bus=event_bus,
        ),
        host=settings.bind_host,
        port=settings.bind_port,
    )


if __name__ == "__main__":
    main()
