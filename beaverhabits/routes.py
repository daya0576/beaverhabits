from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from nicegui import app, ui, context

from beaverhabits.storage.dict import DictHabitList

from beaverhabits.frontend.import_page import import_ui_page
from beaverhabits.frontend.layout import custom_header, redirect
from beaverhabits.frontend.order_page import order_page_ui
from beaverhabits.logging import logger

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
from .frontend.lists_page import lists_page_ui
from .storage.meta import GUI_ROOT_PATH
from .utils import get_display_days, get_user_today_date, reset_week_offset, is_navigating, set_navigating

UNRESTRICTED_PAGE_ROUTES = ("/login", "/register")


def filter_habits_by_list(habit_list: DictHabitList, list_id: str | None = None) -> DictHabitList:
    """Filter habits by list ID."""
    if not list_id:
        logger.debug("No list ID provided, returning all habits")
        logger.debug(f"Total habits: {len(habit_list.data.get('habits', []))}")
        return habit_list
    
    # Create a new list with all data copied
    filtered_data = {
        "habits": [],
        "lists": habit_list.data.get("lists", []).copy(),  # Deep copy lists
        "order": habit_list.data.get("order", []).copy()   # Deep copy order
    }
    filtered_list = DictHabitList(filtered_data)
    
    # Log original habits
    logger.debug(f"Original habits: {len(habit_list.data.get('habits', []))}")
    logger.debug(f"Filtering by list_id: {list_id}")
    
    # Filter habits by list_id
    filtered_habits = []
    for habit in habit_list.data.get("habits", []):
        habit_list_id = habit.get("list_id")
        habit_name = habit.get("name", "unknown")
        logger.debug(f"Checking habit '{habit_name}' (list_id={habit_list_id})")
        
        # Compare as strings to ensure exact matching
        if str(habit_list_id) == str(list_id):
            logger.debug(f"Adding habit '{habit_name}' to filtered list")
            filtered_habits.append(habit.copy())
    
    filtered_list.data["habits"] = filtered_habits
    logger.debug(f"Filtered habits: {len(filtered_habits)}")
    return filtered_list


def get_current_list_id() -> str | None:
    """Get current list ID from query parameters or storage."""
    try:
        # First try to get from URL
        list_id = context.client.page.query.get("list", "")
        logger.debug(f"Raw list ID from query: {list_id}")
        
        if list_id == "None" or not list_id:
            # If not in URL, try storage
            stored_id = app.storage.user.get("current_list")
            logger.debug(f"List ID from storage: {stored_id}")
            if stored_id:
                return stored_id
            
            logger.debug("No list selected")
            return None
        
        # Clean up list ID
        list_id = list_id.strip()
        logger.debug(f"Using list ID from URL: {list_id}")
        
        # Store for persistence
        app.storage.user.update({"current_list": list_id})
        return list_id
    except AttributeError:
        # Try storage as fallback
        stored_id = app.storage.user.get("current_list")
        logger.debug(f"List ID from storage (fallback): {stored_id}")
        return stored_id


@ui.page("/demo")
async def demo_index_page() -> None:
    # Reset to current week only if not navigating
    if not is_navigating():
        reset_week_offset()
    else:
        set_navigating(False)  # Clear navigation flag
    days = await get_display_days()
    habit_list = views.get_or_create_session_habit_list(days)
    await index_page_ui(days, habit_list, None)  # Demo mode doesn't have a user


@ui.page("/demo/add")
async def demo_add_page() -> None:
    days = await get_display_days()
    habit_list = views.get_or_create_session_habit_list(days)
    await add_page_ui(habit_list, None)  # Demo mode doesn't have a user


@ui.page("/demo/order")
async def demo_order_page() -> None:
    days = await get_display_days()
    habit_list = views.get_or_create_session_habit_list(days)
    await order_page_ui(habit_list, None)  # Demo mode doesn't have a user


@ui.page("/demo/habits/{habit_id}")
async def demo_habit_page(habit_id: str) -> None:
    today = await get_user_today_date()
    habit = await views.get_session_habit(habit_id)
    if habit is None:
        redirect("")
        return
    await habit_page_ui(today, habit, None)  # Demo mode doesn't have a user


@ui.page("/demo/habits/{habit_id}/streak")
@ui.page("/demo/habits/{habit_id}/heatmap")
async def demo_habit_page_heatmap(habit_id: str) -> None:
    today = await get_user_today_date()
    habit = await views.get_session_habit(habit_id)
    if habit is None:
        redirect("")
        return
    await heatmap_page(today, habit, None)  # Demo mode doesn't have a user


@ui.page("/demo/export")
async def demo_export() -> None:
    habit_list = views.get_session_habit_list()
    if not habit_list:
        ui.notify("No habits to export", color="negative")
        return
    await views.export_user_habit_list(habit_list, "demo")


@ui.page("/gui/lists")
async def lists_page(user: User = Depends(current_active_user)) -> None:
    lists = await views.get_user_lists(user)
    await lists_page_ui(lists, user)


@ui.page("/gui")
@ui.page("/")
async def index_page(
    user: User = Depends(current_active_user),
) -> None:
    # Reset to current week only if not navigating
    if not is_navigating():
        reset_week_offset()
    else:
        set_navigating(False)  # Clear navigation flag
    days = await get_display_days()
    habit_list = await views.get_user_habit_list(user)
    
    # Create empty habit list if none exists
    if not habit_list:
        habit_list = DictHabitList({"habits": []})
    
    # Filter habits by list if specified
    list_id = get_current_list_id()
    habit_list = filter_habits_by_list(habit_list, list_id)
    
    await index_page_ui(days, habit_list, user)


@ui.page("/gui/add")
async def add_page(user: User = Depends(current_active_user)) -> None:
    habit_list = await views.get_user_habit_list(user)
    if not habit_list:
        habit_list = DictHabitList({"habits": []})
    
    # Don't filter habits in add page since we want to add to main list
    await add_page_ui(habit_list, user)


@ui.page("/gui/order")
async def order_page(user: User = Depends(current_active_user)) -> None:
    habit_list = await views.get_user_habit_list(user)
    if not habit_list:
        habit_list = DictHabitList({"habits": []})
    
    # Filter habits by list if specified
    list_id = get_current_list_id()
    habit_list = filter_habits_by_list(habit_list, list_id)
    
    await order_page_ui(habit_list, user)


@ui.page("/gui/habits/{habit_id}")
async def habit_page(habit_id: str, user: User = Depends(current_active_user)) -> None:
    today = await get_user_today_date()
    habit = await views.get_user_habit(user, habit_id)
    await habit_page_ui(today, habit, user)


@ui.page("/gui/habits/{habit_id}/streak")
@ui.page("/gui/habits/{habit_id}/heatmap")
async def gui_habit_page_heatmap(
    habit_id: str, user: User = Depends(current_active_user)
) -> None:
    habit = await views.get_user_habit(user, habit_id)
    today = await get_user_today_date()
    await heatmap_page(today, habit, user)


@ui.page("/gui/export")
async def gui_export(user: User = Depends(current_active_user)) -> None:
    habit_list = await views.get_user_habit_list(user)
    if not habit_list:
        ui.notify("No habits to export", color="negative")
        return
    await views.export_user_habit_list(habit_list, user.email)


@ui.page("/gui/import")
async def gui_import(user: User = Depends(current_active_user)) -> None:
    await import_ui_page(user)


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
    def handle_exception(exception: Exception):
        if isinstance(exception, HTTPException):
            if exception.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                ui.notify(f"An error occurred: {exception}", type="negative")

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
    app.on_exception(handle_exception)
    ui.run_with(
        fastapi_app,
        title=const.PAGE_TITLE,
        storage_secret=settings.NICEGUI_STORAGE_SECRET,
        favicon="statics/images/favicon.svg",
        dark=True,
    )
