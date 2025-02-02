from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui

from beaverhabits.frontend.import_page import import_ui_page
from beaverhabits.frontend.layout import custom_header
from beaverhabits.frontend.order_page import order_page_ui

from . import const, views
from .app.auth import (
    user_authenticate,
    user_create_token,
)
from .app.crud import get_user_count
from .app.db import User
from .app.dependencies import current_active_user
from .configs import settings
from .frontend.add_page import add_page_ui
from .frontend.cal_heatmap_page import heatmap_page
from .frontend.habit_page import habit_page_ui
from .frontend.index_page import index_page_ui
from .logging import logger
from .storage.meta import GUI_ROOT_PATH
from .utils import dummy_days, get_user_today_date

UNRESTRICTED_PAGE_ROUTES = ("/login", "/register")


@ui.page("/demo")
async def demo_index_page() -> None:
    days = await dummy_days(settings.HABIT_DATE_COLUMNS)
    habit_list = views.get_or_create_session_habit_list(days)
    index_page_ui(days, habit_list)


@ui.page("/demo/add")
async def demo_add_page() -> None:
    days = await dummy_days(settings.HABIT_DATE_COLUMNS)
    habit_list = views.get_or_create_session_habit_list(days)
    add_page_ui(habit_list)


@ui.page("/demo/order")
async def demo_order_page() -> None:
    days = await dummy_days(settings.HABIT_DATE_COLUMNS)
    habit_list = views.get_or_create_session_habit_list(days)
    order_page_ui(habit_list)


@ui.page("/demo/habits/{habit_id}")
async def demo_habit_page(habit_id: str) -> None:
    today = await get_user_today_date()
    habit = await views.get_session_habit(habit_id)
    habit_page_ui(today, habit)


@ui.page("/demo/habits/{habit_id}/streak")
@ui.page("/demo/habits/{habit_id}/heatmap")
async def demo_habit_page_heatmap(habit_id: str) -> None:
    today = await get_user_today_date()
    habit = await views.get_session_habit(habit_id)
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
    days = await dummy_days(settings.HABIT_DATE_COLUMNS)
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
    await views.export_user_habit_list(habit_list, user.email)


@ui.page("/gui/import")
async def gui_import(user: User = Depends(current_active_user)) -> None:
    import_ui_page(user)


@ui.page("/login")
async def login_page() -> Optional[RedirectResponse]:
    custom_header()
    if await views.is_gui_authenticated():
        return RedirectResponse(GUI_ROOT_PATH)

    async def try_login():
        user = await user_authenticate(email=email.value, password=password.value)
        token = user and await user_create_token(user)
        if token is not None:
            app.storage.user.update({"auth_token": token})
            ui.navigate.to(app.storage.user.get("referrer_path", "/"))
        else:
            ui.notify("email or password wrong!", color="negative")

    with ui.card().classes("absolute-center shadow-none w-96"):
        email = ui.input("email").on("keydown.enter", try_login)
        email.classes("w-56")

        password = ui.input("password", password=True, password_toggle_button=True)
        password.on("keydown.enter", try_login)
        password.classes("w-56")

        with ui.element("div").classes("flex mt-4 justify-between items-center"):
            ui.button("Continue", on_click=try_login).props('padding="xs lg"')

        if not await get_user_count() >= settings.MAX_USER_COUNT > 0:
            ui.separator()
            with ui.row():
                ui.label("New around here?").classes("text-sm")
                ui.link("Create account", target="/register").classes("text-sm")


@ui.page("/register")
async def register_page():
    custom_header()
    if await views.is_gui_authenticated():
        return RedirectResponse(GUI_ROOT_PATH)

    async def try_register():
        try:
            await views.validate_max_user_count()
            user = await views.register_user(email=email.value, password=password.value)
            await views.login_user(user)
        except Exception as e:
            ui.notify(str(e), color="negative")
        else:
            ui.navigate.to(app.storage.user.get("referrer_path", "/"))

    await views.validate_max_user_count()
    with ui.card().classes("absolute-center shadow-none w-96"):
        email = ui.input("email").on("keydown.enter", try_register).classes("w-56")
        password = (
            ui.input("password", password=True, password_toggle_button=True)
            .on("keydown.enter", try_register)
            .classes("w-56")
        )

        with ui.element("div").classes("flex mt-4 justify-between items-center"):
            ui.button("Register", on_click=try_register).props('padding="xs lg"')

        ui.separator()
        with ui.row():
            ui.label("Already have an account?")
            ui.link("Log in", target="/login")


def init_gui_routes(fastapi_app: FastAPI):

    @app.middleware("http")
    async def AuthMiddleware(request: Request, call_next):
        auth_token = app.storage.user.get("auth_token")
        if auth_token:
            # Remove original authorization header
            request.scope["headers"] = [
                e for e in request.scope["headers"] if e[0] != b"authorization"
            ]
            # add new authorization header
            request.scope["headers"].append(
                (b"authorization", f"Bearer {auth_token}".encode())
            )

        response = await call_next(request)
        if response.status_code == 401:
            root_path = request.scope["root_path"]
            app.storage.user["referrer_path"] = request.url.path.removeprefix(root_path)
            return RedirectResponse(request.url_for(login_page.__name__))

        return response

    app.add_static_files("/statics", "statics")
    ui.run_with(
        fastapi_app,
        title=const.PAGE_TITLE,
        storage_secret=settings.NICEGUI_STORAGE_SECRET,
        favicon="statics/images/favicon.svg",
        dark=True,
    )
