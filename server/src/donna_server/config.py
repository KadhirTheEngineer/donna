from __future__ import annotations

import os
from dataclasses import dataclass
from ipaddress import ip_address

from psycopg import ProgrammingError
from psycopg.conninfo import conninfo_to_dict


class ConfigurationError(ValueError):
    """Raised when server configuration is unsafe or invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str = "demo"
    bind_host: str = "127.0.0.1"
    bind_port: int = 8742
    pairing_ttl_seconds: int = 300
    replay_window_seconds: int = 120
    database_dsn: str | None = None

    @classmethod
    def from_environment(cls) -> Settings:
        settings = cls(
            environment=os.getenv("DONNA_ENVIRONMENT", "demo"),
            bind_host=os.getenv("DONNA_BIND_HOST", "127.0.0.1"),
            bind_port=int(os.getenv("DONNA_BIND_PORT", "8742")),
            pairing_ttl_seconds=int(os.getenv("DONNA_PAIRING_TTL_SECONDS", "300")),
            replay_window_seconds=int(os.getenv("DONNA_REPLAY_WINDOW_SECONDS", "120")),
            database_dsn=os.getenv("DONNA_DATABASE_DSN"),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.environment not in {"demo", "development", "production"}:
            raise ConfigurationError("DONNA_ENVIRONMENT must be demo, development, or production")
        try:
            address = ip_address(self.bind_host)
        except ValueError as error:
            raise ConfigurationError(
                "DONNA_BIND_HOST must be a literal loopback address"
            ) from error
        if not address.is_loopback:
            raise ConfigurationError(
                "non-loopback binding is disabled until encrypted transport is configured"
            )
        if not 1 <= self.bind_port <= 65535:
            raise ConfigurationError("DONNA_BIND_PORT must be between 1 and 65535")
        if not 60 <= self.pairing_ttl_seconds <= 900:
            raise ConfigurationError("DONNA_PAIRING_TTL_SECONDS must be between 60 and 900")
        if not 30 <= self.replay_window_seconds <= 300:
            raise ConfigurationError("DONNA_REPLAY_WINDOW_SECONDS must be between 30 and 300")
        if self.database_dsn is not None:
            try:
                database = conninfo_to_dict(self.database_dsn)
            except ProgrammingError as error:
                raise ConfigurationError("DONNA_DATABASE_DSN is invalid") from error
            host = database.get("host")
            if host not in {None, "", "localhost", "127.0.0.1", "::1"}:
                raise ConfigurationError("DONNA_DATABASE_DSN must use a loopback host")
            if database.get("password"):
                raise ConfigurationError(
                    "DONNA_DATABASE_DSN must not contain a password; "
                    "use reviewed credential resolution"
                )
            if not database.get("dbname"):
                raise ConfigurationError("DONNA_DATABASE_DSN must name a database")
