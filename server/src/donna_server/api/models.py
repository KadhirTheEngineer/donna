from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PairingCodeResponse(StrictModel):
    code: str = Field(pattern=r"^\d{6}$")
    expires_at: datetime


class PairingRequest(StrictModel):
    code: str = Field(pattern=r"^\d{6}$")
    friendly_name: str = Field(min_length=1, max_length=80)
    capabilities: list[str] = Field(default_factory=list, max_length=32)
    public_key: str = Field(min_length=43, max_length=44)


class PairingResponse(StrictModel):
    device_id: str
    issued_at: datetime
    authentication: Literal["ed25519-v1"] = "ed25519-v1"


class ErrorResponse(StrictModel):
    code: str
    message: str
    request_id: str
    retryable: bool
    fields: dict[str, Any] = Field(default_factory=dict)
