import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from donna_server.adapters.local_health import FakeHealthProbe
from donna_server.adapters.memory_identity import MemoryIdentityRepository
from donna_server.api.models import PairingCodeResponse, PairingRequest, PairingResponse
from donna_server.application.dashboard import FixtureDashboardService
from donna_server.application.identity import IdentityService
from donna_server.config import ConfigurationError, Settings
from donna_server.domain.dashboard import DashboardService
from donna_server.domain.errors import DonnaError
from donna_server.domain.events import EventBus
from donna_server.domain.health import HealthProbe
from donna_server.domain.identity import DeviceCredential, IdentityRepository
from donna_server.events.memory import MemoryEventBus

LOGGER = logging.getLogger("donna.request")


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", f"request_{uuid4().hex}")


def _log_request(
    request: Request, status_code: int, started: float, error_category: str | None
) -> None:
    record = {
        "component": "api",
        "event": "request.completed",
        "request_id": request.state.request_id,
        "trace_id": request.state.trace_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        "error_category": error_category or getattr(request.state, "error_category", None),
    }
    LOGGER.info("%s", json.dumps(record, sort_keys=True, separators=(",", ":")))


def _is_loopback_client(host: str | None) -> bool:
    return host in {"127.0.0.1", "::1", "testclient"}


def create_app(
    settings: Settings | None = None,
    health_probe: HealthProbe | None = None,
    dashboard_service: DashboardService | None = None,
    identity_repository: IdentityRepository | None = None,
    event_bus: EventBus | None = None,
) -> FastAPI:
    active_settings = settings or Settings.from_environment()
    active_settings.validate()
    if active_settings.environment == "production" and (
        identity_repository is None or event_bus is None
    ):
        raise ConfigurationError(
            "production mode requires the durable identity and event repository adapters"
        )
    ephemeral = identity_repository is None or event_bus is None
    active_identity_repository = identity_repository or MemoryIdentityRepository()
    identity = IdentityService(
        active_identity_repository,
        active_settings.pairing_ttl_seconds,
        active_settings.replay_window_seconds,
    )
    dashboard = dashboard_service or FixtureDashboardService(
        _repository_root() / "contracts" / "examples" / "dashboard-snapshot.v1.json"
    )
    events = event_bus or MemoryEventBus()
    host_health = health_probe or FakeHealthProbe()

    app = FastAPI(title="Donna laptop service", version="1.0.0")
    app.state.settings = active_settings
    app.state.identity = identity
    app.state.dashboard = dashboard
    app.state.events = events

    @app.middleware("http")
    async def request_context(request: Request, call_next: Any) -> Any:
        request.state.request_id = f"request_{uuid4().hex}"
        request.state.trace_id = f"trace_{uuid4().hex}"
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            _log_request(request, 500, started, "internal")
            raise
        response.headers["X-Donna-Request-Id"] = request.state.request_id
        response.headers["X-Donna-Trace-Id"] = request.state.trace_id
        _log_request(request, response.status_code, started, None)
        return response

    @app.exception_handler(DonnaError)
    async def donna_error(request: Request, error: DonnaError) -> JSONResponse:
        request.state.error_category = error.code
        return JSONResponse(
            status_code=error.status_code,
            content={
                "code": error.code,
                "message": error.safe_message,
                "request_id": _request_id(request),
                "retryable": error.retryable,
                "fields": error.fields,
            },
        )

    def authenticate(
        request: Request,
        device_id: Annotated[str | None, Header(alias="X-Donna-Device-Id")] = None,
        timestamp: Annotated[str | None, Header(alias="X-Donna-Timestamp")] = None,
        nonce: Annotated[str | None, Header(alias="X-Donna-Nonce")] = None,
        signature: Annotated[str | None, Header(alias="X-Donna-Signature")] = None,
    ) -> DeviceCredential:
        if None in {device_id, timestamp, nonce, signature}:
            raise DonnaError(
                "authentication_failed",
                "Device authentication failed. Pair this device again if the problem continues.",
                401,
            )
        assert device_id is not None
        assert timestamp is not None
        assert nonce is not None
        assert signature is not None
        return identity.authenticate(
            device_id=device_id,
            timestamp_text=timestamp,
            nonce=nonce,
            signature=signature,
            method=request.method,
            path=request.url.path,
        )

    @app.get("/v1/health")
    def health() -> dict[str, Any]:
        components = [
            {
                "component": "api",
                "state": "healthy",
                "last_success": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "last_error_category": None,
                "dependencies": [],
                "remediation": None,
                "details": {},
            },
            {
                "component": "identity_store",
                "state": "degraded" if ephemeral else "healthy",
                "last_success": (
                    None if ephemeral else datetime.now(UTC).isoformat().replace("+00:00", "Z")
                ),
                "last_error_category": "ephemeral_demo_store" if ephemeral else None,
                "dependencies": ["postgresql"],
                "remediation": (
                    "Demo pairing is lost on restart. Configure the PostgreSQL adapter "
                    "before production use."
                    if ephemeral
                    else None
                ),
                "details": {"durable": not ephemeral},
            },
            {
                "component": "dashboard",
                "state": "degraded",
                "last_success": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "last_error_category": "demo_fixture",
                "dependencies": [],
                "remediation": (
                    "Dashboard data is a sanitized fixture until connectors are configured."
                ),
                "details": {"adapter": "fixture"},
            },
            *host_health.snapshot(),
        ]
        return {
            "status": "degraded",
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "components": components,
        }

    @app.post("/v1/pairing/codes", response_model=PairingCodeResponse)
    def issue_pairing_code(request: Request) -> PairingCodeResponse:
        if not _is_loopback_client(request.client.host if request.client else None):
            raise DonnaError(
                "pairing_code_local_only",
                "Pairing codes can only be created from the laptop loopback interface.",
                403,
            )
        code, expires_at = identity.create_pairing_code()
        return PairingCodeResponse(code=code, expires_at=expires_at)

    @app.post("/v1/pairing/complete", response_model=PairingResponse)
    def complete_pairing(pairing: PairingRequest) -> PairingResponse:
        credential = identity.pair_device(
            pairing.code,
            pairing.friendly_name,
            tuple(sorted(set(pairing.capabilities))),
            pairing.public_key,
        )
        return PairingResponse(
            device_id=credential.device_id,
            issued_at=credential.issued_at,
        )

    @app.get("/v1/dashboard")
    def dashboard_snapshot(
        device: Annotated[DeviceCredential, Depends(authenticate)],
        window: str = "today",
    ) -> dict[str, Any]:
        if "dashboard.read" not in device.capabilities:
            raise DonnaError("capability_denied", "This device cannot read the dashboard.", 403)
        if window != "today":
            raise DonnaError("window_unsupported", "Only the today dashboard is available.", 400)
        return dashboard.snapshot()

    @app.post("/v1/demo/dashboard/invalidate")
    def invalidate_demo_dashboard(request: Request) -> dict[str, Any]:
        if active_settings.environment != "demo" or not _is_loopback_client(
            request.client.host if request.client else None
        ):
            raise DonnaError(
                "demo_endpoint_unavailable",
                "The demo invalidation endpoint is only available on laptop loopback.",
                404,
            )
        return events.publish(
            "dashboard.invalidated",
            "dashboard:today",
            f"trace_{uuid4().hex}",
            {"reason": "manual_demo_invalidation"},
        )

    @app.websocket("/v1/events")
    async def event_stream(websocket: WebSocket, after: int = 0) -> None:
        try:
            device = identity.authenticate(
                device_id=websocket.headers["X-Donna-Device-Id"],
                timestamp_text=websocket.headers["X-Donna-Timestamp"],
                nonce=websocket.headers["X-Donna-Nonce"],
                signature=websocket.headers["X-Donna-Signature"],
                method="GET",
                path="/v1/events",
            )
            if "events.read" not in device.capabilities:
                raise DonnaError("capability_denied", "This device cannot read events.", 403)
        except (DonnaError, KeyError):
            await websocket.close(code=4401, reason="device authentication failed")
            return
        subscriber = events.subscribe()
        replay, retained = events.replay_after(after)
        await websocket.accept()
        if not retained:
            await websocket.send_json(
                events.publish(
                    "events.replay_expired",
                    None,
                    f"trace_{uuid4().hex}",
                    {"required_action": "refresh_snapshot"},
                )
            )
        for event in replay:
            await websocket.send_json(event)
        try:
            while True:
                event_task = asyncio.create_task(subscriber.get())
                receive_task = asyncio.create_task(websocket.receive_text())
                tasks = {event_task, receive_task}
                try:
                    done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    if receive_task in done:
                        receive_task.result()
                        continue
                    await websocket.send_json(event_task.result())
                finally:
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        finally:
            events.unsubscribe(subscriber)

    return app
