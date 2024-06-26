from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from nicegui import app, ui

from . import const
from .utils import dummy_days, get_user_today_date
from .app.auth import (
    user_authenticate,
    user_check_token,
    user_create,
    user_create_token,
)
from .app.db import User
from .app.users import current_active_user
from .configs import settings
from .frontend.add_page import add_page_ui
from .frontend.habit_page import habit_page_ui
from .frontend.index_page import index_page_ui
from .frontend.cal_heatmap_page import heatmap_page
from .storage.meta import GUI_ROOT_PATH
from . import views


UNRESTRICTED_PAGE_ROUTES = ("/login", "/register", "/demo", "/demo/add")


@ui.page("/demo")
async def demo_index_page() -> None:
    days = await dummy_days(settings.INDEX_HABIT_ITEM_COUNT)
    habit_list = views.get_or_create_session_habit_list(days)
    index_page_ui(days, habit_list)


@ui.page("/demo/add")
async def demo_add_page() -> None:
    days = await dummy_days(settings.INDEX_HABIT_ITEM_COUNT)
    habit_list = views.get_or_create_session_habit_list(days)
    add_page_ui(habit_list)


@ui.page("/demo/habits/{habit_id}")
async def demo_habit_page(habit_id: str) -> None:
    today = await get_user_today_date()
    habit = await views.get_session_habit(habit_id)
    habit_page_ui(today, habit)


@ui.page("/gui")
@ui.page("/")
async def index_page(
    user: User = Depends(current_active_user),
) -> None:
    days = await dummy_days(settings.INDEX_HABIT_ITEM_COUNT)
    habits = await views.get_or_create_user_habit_list(user, days)
    index_page_ui(days, habits)


@ui.page("/gui/add")
async def add_page(user: User = Depends(current_active_user)) -> None:
    days = await dummy_days(settings.INDEX_HABIT_ITEM_COUNT)
    habits = await views.get_or_create_user_habit_list(user, days)
    add_page_ui(habits)


@ui.page("/gui/habits/{habit_id}")
async def habit_page(habit_id: str, user: User = Depends(current_active_user)) -> None:
    today = await get_user_today_date()
    habit = await views.get_user_habit(user, habit_id)
    habit_page_ui(today, habit)


@ui.page("/gui/habits/{habit_id}/heatmap")
async def gui_habit_page_heatmap(
    habit_id: str, user: User = Depends(current_active_user)
) -> None:
    habit = await views.get_user_habit(user, habit_id)
    today = await get_user_today_date()
    heatmap_page(today, habit)


@ui.page("/login")
async def login_page() -> Optional[RedirectResponse]:
    async def try_login():
        user = await user_authenticate(email=email.value, password=password.value)
        token = user and await user_create_token(user)
        if token is not None:
            app.storage.user.update({"auth_token": token})
            ui.navigate.to(app.storage.user.get("referrer_path", "/"))
        else:
            ui.notify("email or password wrong!", color="negative")

    if await user_check_token(app.storage.user.get("auth_token", None)):
        return RedirectResponse(GUI_ROOT_PATH)

    with ui.card().classes("absolute-center shadow-none w-96"):
        email = ui.input("email").on("keydown.enter", try_login)
        password = ui.input("password", password=True, password_toggle_button=True).on(
            "keydown.enter", try_login
        )
        ui.button("Continue", on_click=try_login).props('padding="xs lg"')
        ui.separator()
        with ui.row():
            ui.label("New around here?").classes("text-sm")
            ui.link("Create account", target="/register").classes("text-sm")


@ui.page("/register")
async def register():
    async def try_register():
        try:
            user = await user_create(email=email.value, password=password.value)
        except Exception as e:
            ui.notify(str(e))
        else:
            token = user and await user_create_token(user)
            if token is not None:
                app.storage.user.update({"auth_token": token})
                ui.navigate.to(app.storage.user.get("referrer_path", "/"))

    with ui.card().classes("absolute-center shadow-none w-96"):
        email = ui.input("email").on("keydown.enter", try_register)
        password = ui.input("password", password=True, password_toggle_button=True).on(
            "keydown.enter", try_register
        )

        with ui.element("div").classes("flex mt-4 justify-between items-center"):
            ui.button("Register", on_click=try_register)
        ui.separator()
        with ui.row():
            ui.label("Already have an account?")
            ui.link("Log in", target="/login")


def init_gui_routes(fastapi_app: FastAPI):
    @app.middleware("http")
    async def AuthMiddleware(request: Request, call_next):
        client_page_routes = [
            route.path for route in app.routes if isinstance(route, APIRoute)
        ]
        if not await user_check_token(app.storage.user.get("auth_token", None)):
            if (
                request.url.path in client_page_routes
                and request.url.path not in UNRESTRICTED_PAGE_ROUTES
            ):
                root_path = request.scope["root_path"]
                app.storage.user["referrer_path"] = request.url.path.removeprefix(
                    root_path
                )
                return RedirectResponse(request.url_for(login_page.__name__))

        # Remove original authorization header
        request.scope["headers"] = [
            e for e in request.scope["headers"] if not e[0] == b"authorization"
        ]
        # # add new authorization header
        request.scope["headers"].append(
            (b"authorization", f"Bearer {app.storage.user.get('auth_token')}".encode())
        )

        return await call_next(request)

    ui.run_with(
        fastapi_app,
        title=const.PAGE_TITLE,
        storage_secret=settings.NICEGUI_STORAGE_SECRET,
        favicon="images/favicon.svg",
        dark=True,
    )
