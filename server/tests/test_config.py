from __future__ import annotations

import pytest
from donna_server.config import ConfigurationError, Settings


def test_non_loopback_binding_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="non-loopback"):
        Settings(bind_host="192.0.2.10").validate()


def test_default_configuration_is_valid() -> None:
    Settings().validate()


def test_production_refuses_ephemeral_repositories() -> None:
    from donna_server.api.app import create_app

    with pytest.raises(ConfigurationError, match="durable identity"):
        create_app(Settings(environment="production"))
