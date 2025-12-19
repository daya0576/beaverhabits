import time
from urllib.parse import urljoin

import httpx
from fastapi import Form, HTTPException
from fastapi.responses import RedirectResponse
from loguru import logger
from nicegui import app, ui

from beaverhabits import views
from beaverhabits.app import auth
from beaverhabits.configs import settings


def google_one_tap_login() -> None:
    if not settings.GOOGLE_ONE_TAP_ENABLED:
        return

    logger.info("Google One Tap login is enabled")
    user_info = app.storage.user.get("user_info", {})
    if not _is_valid(user_info):
        logger.info(
            "User not logged in, showing Google One Tap prompt,"
            f"callback: {settings.GOOGLE_ONE_TAP_CALLBACK_URL}"
        )
        ui.add_head_html(
            '<script src="https://accounts.google.com/gsi/client" async defer></script>'
        )
        ui.html(
            f"""
            <div id="g_id_onload"
                data-client_id="{settings.GOOGLE_ONE_TAP_CLIENT_ID}"
                data-login_uri="{settings.GOOGLE_ONE_TAP_CALLBACK_URL}">
            </div>
            """,
            sanitize=False,
        )
        return


@app.post("/google/auth")
async def google_auth(credential: str = Form(...)) -> RedirectResponse:
    logger.info("Authenticating Google One Tap token")
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        )
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid token")
    user_info = response.json()
    if not _is_valid(user_info):
        raise HTTPException(status_code=400, detail="Invalid token claims")

    logger.info(
        f"Google One Tap authentication successful for {user_info.get('email')}"
    )

    app.storage.user["user_info"] = user_info
    user = await auth.user_get_or_create_by_email(user_info.get("email"))
    await views.login_user(user)

    return RedirectResponse("/gui", status_code=303)


def _is_valid(user_info: dict) -> bool:
    try:
        return all(
            [
                int(user_info.get("exp", 0)) > int(time.time()),
                user_info.get("aud") == settings.GOOGLE_ONE_TAP_CLIENT_ID,
                user_info.get("iss")
                in {"https://accounts.google.com", "accounts.google.com"},
                str(user_info.get("email_verified")).lower() == "true",
            ]
        )
    except Exception:
        return False
