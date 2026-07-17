from __future__ import annotations

import hashlib
import os
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict

ROOT = Path(__file__).resolve().parents[1]
LOCK_ID = 4_461_116_097


def main() -> None:
    dsn = os.getenv("DONNA_DATABASE_DSN")
    if not dsn:
        raise SystemExit("DONNA_DATABASE_DSN is required; it is never printed")
    parameters = conninfo_to_dict(dsn)
    if parameters.get("host") not in {None, "", "localhost", "127.0.0.1", "::1"}:
        raise SystemExit("migration runner permits only a local PostgreSQL host")
    migrations = sorted((ROOT / "server" / "migrations").glob("*.sql"))
    with psycopg.connect(dsn) as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_ID,))
        connection.execute("CREATE SCHEMA IF NOT EXISTS service")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS service.schema_migrations (
                version text PRIMARY KEY,
                sha256 text NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        applied: dict[str, str] = dict(
            connection.execute("SELECT version, sha256 FROM service.schema_migrations").fetchall()
        )
        for migration in migrations:
            sql = migration.read_text(encoding="utf-8")
            digest = hashlib.sha256(sql.encode()).hexdigest()
            if migration.name in applied:
                if applied[migration.name] != digest:
                    raise SystemExit(f"applied migration checksum changed: {migration.name}")
                print(f"current: {migration.name}")
                continue
            connection.execute(sql)
            connection.execute(
                "INSERT INTO service.schema_migrations (version, sha256) VALUES (%s, %s)",
                (migration.name, digest),
            )
            print(f"applied: {migration.name}")


if __name__ == "__main__":
    main()
