import time
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from nicegui import Client, app, ui

from beaverhabits import const, views
from beaverhabits.app.auth import (
    user_authenticate,
)
from beaverhabits.app.crud import get_user_count
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import (
    current_active_user,
    current_admin_user,
    get_reset_user,
)
from beaverhabits.configs import settings
from beaverhabits.frontend import paddle_page
from beaverhabits.frontend.add_page import add_page_ui
from beaverhabits.frontend.admin import admin_page
from beaverhabits.frontend.components import (
    auth_card,
    auth_email,
    auth_forgot_password,
    auth_password,
    auth_redirect,
)
from beaverhabits.frontend.export_page import export_page
from beaverhabits.frontend.habit_page import habit_page_ui
from beaverhabits.frontend.import_page import import_ui_page
from beaverhabits.frontend.index_page import index_page_ui
from beaverhabits.frontend.layout import custom_headers, redirect
from beaverhabits.frontend.order_page import order_page_ui
from beaverhabits.frontend.streaks import heatmap_page
from beaverhabits.logger import logger
from beaverhabits.storage.meta import GUI_ROOT_PATH
from beaverhabits.utils import dummy_days, get_user_today_date

UNRESTRICTED_PAGE_ROUTES = ("/login", "/register")


@ui.page("/demo")
async def demo_index_page() -> None:
    days = await dummy_days(settings.INDEX_HABIT_DATE_COLUMNS)
    habit_list = views.get_or_create_session_habit_list(days)
    index_page_ui(days, habit_list)


@ui.page("/demo/add")
async def demo_add_page() -> None:
    days = await dummy_days(settings.INDEX_HABIT_DATE_COLUMNS)
    habit_list = views.get_or_create_session_habit_list(days)
    add_page_ui(habit_list)


@ui.page("/demo/order")
async def demo_order_page() -> None:
    days = await dummy_days(settings.INDEX_HABIT_DATE_COLUMNS)
    habit_list = views.get_or_create_session_habit_list(days)
    order_page_ui(habit_list)


@ui.page("/demo/habits/{habit_id}")
async def demo_habit_page(habit_id: str) -> None:
    today = await get_user_today_date()
    habit = await views.get_session_habit(habit_id)
    if habit is None:
        redirect("")
        return
    habit_page_ui(today, habit)


@ui.page("/demo/habits/{habit_id}/streak")
@ui.page("/demo/habits/{habit_id}/heatmap")
async def demo_habit_page_heatmap(habit_id: str) -> None:
    today = await get_user_today_date()
    habit = await views.get_session_habit(habit_id)
    if habit is None:
        redirect("")
        return
    heatmap_page(today, habit)


@ui.page("/demo/export")
async def demo_export() -> None:
    habit_list = views.get_session_habit_list()
    if not habit_list:
        ui.notify("No habits to export", color="negative")
        return
    await views.export_user_habit_list(habit_list, "demo")


@ui.page("/gui")
@ui.page("/")
async def index_page(
    user: User = Depends(current_active_user),
) -> None:
    days = await dummy_days(settings.INDEX_HABIT_DATE_COLUMNS)
    habit_list = await views.get_user_habit_list(user)
    index_page_ui(days, habit_list)


@ui.page("/gui/add")
async def add_page(user: User = Depends(current_active_user)) -> None:
    habit_list = await views.get_user_habit_list(user)
    add_page_ui(habit_list)


@ui.page("/gui/order")
async def order_page(user: User = Depends(current_active_user)) -> None:
    habit_list = await views.get_user_habit_list(user)
    order_page_ui(habit_list)


@ui.page("/gui/habits/{habit_id}")
async def habit_page(habit_id: str, user: User = Depends(current_active_user)) -> None:
    today = await get_user_today_date()
    habit = await views.get_user_habit(user, habit_id)
    habit_page_ui(today, habit)


@ui.page("/gui/habits/{habit_id}/streak")
@ui.page("/gui/habits/{habit_id}/heatmap")
async def gui_habit_page_heatmap(
    habit_id: str, user: User = Depends(current_active_user)
) -> None:
    habit = await views.get_user_habit(user, habit_id)
    today = await get_user_today_date()
    heatmap_page(today, habit)


@ui.page("/gui/export")
async def gui_export(user: User = Depends(current_active_user)) -> None:
    habit_list = await views.get_user_habit_list(user)
    if not habit_list:
        ui.notify("No habits to export", color="negative")
        return
    await export_page(habit_list, user)


@ui.page("/gui/import")
async def gui_import(user: User = Depends(current_active_user)) -> None:
    import_ui_page(user)


@ui.page("/login")
async def login_page(client: Client) -> Optional[RedirectResponse]:
    custom_headers()
    if await views.is_gui_authenticated():
        return RedirectResponse(GUI_ROOT_PATH)

    async def try_login():
        if not email.value:
            ui.notify("Email is required", color="negative")
            return
        if not password.value:
            ui.notify("Password is required", color="negative")
            return

        logger.info(f"Trying to login with {email.value}")
        user = await user_authenticate(email=email.value, password=password.value)
        if user:
            await views.login_user(user)
            ui.navigate.to(GUI_ROOT_PATH)
        else:
            ui.notify("email or password wrong!", color="negative")

    try:
        # Wait for the handshake before sending events to the server
        await client.connected(timeout=3)
    except TimeoutError:
        # Ignore weak dependency
        logger.warning("Client not connected, skipping...")

    with auth_card(title="Sign in", func=try_login):
        email = auth_email()
        password = auth_password().on("keydown.enter", try_login)

        with ui.row().classes("gap-2 w-full items-center"):
            auth_forgot_password(email, views.forgot_password)
            ui.space()
            if not await get_user_count() >= settings.MAX_USER_COUNT > 0:
                auth_redirect("Create account", "/register")


@ui.page("/register")
async def register_page():
    custom_headers()
    if await views.is_gui_authenticated():
        return RedirectResponse(GUI_ROOT_PATH)

    async def try_register():
        if not email.value:
            ui.notify("Email is required", color="negative")
            return
        if (
            not password1.value
            or not password2.value
            or password1.value != password2.value
        ):
            ui.notify("Passwords do not match", color="negative")
            return

        try:
            await views.validate_max_user_count()
            user = await views.register_user(
                email=email.value, password=password2.value
            )
            await views.login_user(user)
        except Exception as e:
            ui.notify(str(e), color="negative")
        else:
            ui.navigate.to(GUI_ROOT_PATH)

    await views.validate_max_user_count()

    with auth_card(title="Sign up", func=try_register):
        email = auth_email()
        password1 = auth_password().on("keydown.enter", try_register)
        password2 = auth_password("Confirm password").on("keydown.enter", try_register)

        with ui.row().classes("gap-2 w-full items-center"):
            auth_forgot_password(email, views.forgot_password)
            ui.space()
            auth_redirect("Sign in", "/login")


@ui.page("/reset-password")
async def forgot_password_page(user: User = Depends(get_reset_user)):
    custom_headers()

    async def try_reset():
        if not password1.value or not password2.value:
            ui.notify("Password is required", color="negative")
            return
        if password1.value != password2.value:
            ui.notify("Passwords do not match", color="negative")
            return

        logger.info(f"Trying to reset password for {user.email}")
        await views.reset_password(user, password1.value)

    with auth_card(title="Reset password", func=try_reset):
        auth_email(user.email).disable()
        password1 = auth_password("New password")
        password2 = auth_password("Confirm password")


if settings.ENABLE_PLAN:
    from beaverhabits.frontend.paddle_page import PRIVACY, TERMS
    from beaverhabits.frontend.pricing_page import landing_page

    @ui.page("/")
    @ui.page("/pricing")
    async def pricing_page():
        await landing_page()

    @ui.page("/terms")
    def terms_page():
        paddle_page.markdown(TERMS)

    @ui.page("/privacy")
    def privacy_page():
        paddle_page.markdown(PRIVACY)

    @ui.page("/admin", include_in_schema=False)
    async def admin(user: User = Depends(current_admin_user)):
        await admin_page(user)

    @ui.page("/admin/backup", include_in_schema=False)
    async def manual_backup(user: User = Depends(current_admin_user)):
        logger.info(f"Starting backup, triggered by {user.email}")
        await views.backup_all_users()


def init_gui_routes(fastapi_app: FastAPI):
    def handle_exception(exception: Exception):
        if isinstance(exception, HTTPException):
            if exception.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                ui.notify(f"An error occurred: {exception}", type="negative")

    @app.middleware("http")
    async def AuthMiddleware(request: Request, call_next):
        logger.debug(f"AuthMiddleware: {request.url.path}")
        if token := app.storage.user.get("auth_token"):
            # Remove original authorization header
            request.scope["headers"] = [
                e for e in request.scope["headers"] if e[0] != b"authorization"
            ]
            # add new authorization header
            request.scope["headers"].append(
                (b"authorization", f"Bearer {token}".encode())
            )

        response = await call_next(request)
        if response.status_code == 401:
            # root_path = request.scope["root_path"]
            # app.storage.user["referrer_path"] = request.url.path.removeprefix(root_path)
            return RedirectResponse(request.url_for(login_page.__name__))

        return response

    @app.middleware("http")
    async def StaticFilesCacheMiddleware(request: Request, call_next):
        response = await call_next(request)

        path = request.url.path
        if path.startswith("/_nicegui/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    oneyear = 365 * 24 * 60 * 60
    app.add_static_files("/statics", "statics", max_cache_age=oneyear)
    app.on_exception(handle_exception)
    ui.run_with(
        fastapi_app,
        title=const.PAGE_TITLE,
        storage_secret=settings.NICEGUI_STORAGE_SECRET,
        favicon="statics/images/favicon.svg",
        binding_refresh_interval=0.05,
        dark=None,
    )
