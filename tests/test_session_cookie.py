import base64
import json
import time
from types import SimpleNamespace
from unittest.mock import patch

import itsdangerous
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from beaverhabits.configs import settings
from beaverhabits.routes.routes import (
    SESSION_REFRESH_KEY,
    init_gui_routes,
    maybe_refresh_session,
)


def _make_request(path: str, session: dict | None = None) -> Request:
    scope: dict = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
    }
    if session is not None:
        scope["session"] = session
    return Request(scope)


def _decode_session_cookie(cookie_value: str, secret: str) -> dict:
    signer = itsdangerous.TimestampSigner(secret)
    raw = signer.unsign(cookie_value.encode("utf-8"), max_age=settings.NICEGUI_SESSION_MAX_AGE_SECONDS)
    return json.loads(base64.b64decode(raw))


def test_default_session_cookie_settings() -> None:
    assert settings.NICEGUI_SESSION_MAX_AGE_SECONDS == 365 * 24 * 60 * 60
    assert settings.NICEGUI_SESSION_REFRESH_INTERVAL_SECONDS == 24 * 60 * 60
    assert settings.NICEGUI_SESSION_HTTPS_ONLY is False


def test_maybe_refresh_session_respects_interval_and_static_paths() -> None:
    session: dict = {"id": "user-1"}
    req = _make_request("/gui", session)

    assert maybe_refresh_session(req, now=1_000, refresh_interval=86_400) is True
    assert session[SESSION_REFRESH_KEY] == 1_000

    # Within refresh interval -> no-op
    assert maybe_refresh_session(req, now=1_000 + 3_600, refresh_interval=86_400) is False
    assert session[SESSION_REFRESH_KEY] == 1_000

    # Past refresh interval -> slides forward
    assert maybe_refresh_session(req, now=1_000 + 86_400, refresh_interval=86_400) is True
    assert session[SESSION_REFRESH_KEY] == 1_000 + 86_400

    # Static paths are never refreshed
    static_session: dict = {"id": "user-2"}
    assert maybe_refresh_session(_make_request("/_nicegui/test.js", static_session), now=1_000) is False
    assert maybe_refresh_session(_make_request("/statics/logo.png", static_session), now=1_000) is False
    assert SESSION_REFRESH_KEY not in static_session


def test_session_middleware_upgrades_legacy_cookie_and_slides() -> None:
    secret = "dev"
    max_age = settings.NICEGUI_SESSION_MAX_AGE_SECONDS
    test_app = FastAPI()
    storage_state = SimpleNamespace(authenticated=True)

    @test_app.middleware("http")
    async def auth_like_middleware(request: Request, call_next):
        response = await call_next(request)
        if response.status_code < 400 and storage_state.authenticated:
            maybe_refresh_session(request)
        return response

    test_app.add_middleware(SessionMiddleware, secret_key=secret, max_age=max_age)

    @test_app.get("/gui")
    async def gui_endpoint():
        return Response("ok")

    @test_app.get("/unauth")
    async def unauth_endpoint():
        return Response("unauthorized", status_code=401)

    # Craft a legacy cookie without refreshed_at (1 day old, same format as old 14-day cookies)
    base_time = int(time.time()) - 200_000
    signer = itsdangerous.TimestampSigner(secret)
    legacy_payload = base64.b64encode(json.dumps({"id": "legacy-session-id"}).encode("utf-8"))
    with patch("time.time", return_value=base_time - 86_400):
        legacy_cookie = signer.sign(legacy_payload).decode("utf-8")

    client = TestClient(test_app)
    client.cookies.set("session", legacy_cookie, domain="testserver.local")

    # 1. Legacy cookie seamlessly upgraded on first authenticated visit
    with patch("beaverhabits.routes.routes.time.time", return_value=base_time):
        resp1 = client.get("/gui")
    assert resp1.status_code == 200
    set_cookie1 = resp1.headers.get("set-cookie", "")
    assert f"Max-Age={max_age}" in set_cookie1
    data1 = _decode_session_cookie(resp1.cookies["session"], secret)
    assert data1["id"] == "legacy-session-id"
    assert data1[SESSION_REFRESH_KEY] == base_time

    # 2. Visit within 24h does not re-issue Set-Cookie
    with patch("beaverhabits.routes.routes.time.time", return_value=base_time + 3_600):
        resp2 = client.get("/gui")
    assert resp2.status_code == 200
    assert "set-cookie" not in resp2.headers

    # 3. 401 response does not refresh even after 24h
    with patch("beaverhabits.routes.routes.time.time", return_value=base_time + 90_000):
        resp_unauth = client.get("/unauth")
    assert resp_unauth.status_code == 401
    assert "set-cookie" not in resp_unauth.headers

    # 4. Visit after 24h slides expiration forward by another 365 days
    with patch("beaverhabits.routes.routes.time.time", return_value=base_time + 90_000):
        resp3 = client.get("/gui")
    assert resp3.status_code == 200
    set_cookie3 = resp3.headers.get("set-cookie", "")
    assert f"Max-Age={max_age}" in set_cookie3
    data3 = _decode_session_cookie(resp3.cookies["session"], secret)
    assert data3["id"] == "legacy-session-id"
    assert data3[SESSION_REFRESH_KEY] == base_time + 90_000


def test_init_gui_routes_passes_session_middleware_kwargs() -> None:
    dummy_app = FastAPI()
    with patch("beaverhabits.routes.routes.ui.run_with") as mock_run_with, patch(
        "beaverhabits.routes.routes.app"
    ):
        init_gui_routes(dummy_app)

    mock_run_with.assert_called_once()
    kwargs = mock_run_with.call_args.kwargs
    assert kwargs["session_middleware_kwargs"] == {
        "max_age": settings.NICEGUI_SESSION_MAX_AGE_SECONDS,
        "https_only": settings.NICEGUI_SESSION_HTTPS_ONLY,
    }
