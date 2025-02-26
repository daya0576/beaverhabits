from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from nicegui import app, ui, context

from beaverhabits.frontend.import_page import import_ui_page
from beaverhabits.frontend.layout import custom_header, redirect
from beaverhabits.frontend.order_page import order_page_ui
from beaverhabits.logging import logger

from . import const, views
from .app.auth import (
    user_authenticate,
    user_create_token,
)
from .app.crud import get_user_count, get_user_habits, get_user_lists
from .app.db import User
from .app.dependencies import current_active_user
from .configs import settings
from .frontend.add_page import add_page_ui
from .frontend.cal_heatmap_page import heatmap_page
from .frontend.habit_page import habit_page_ui
from .frontend.index_page import index_page_ui
from .frontend.lists_page import lists_page_ui
from .utils import get_display_days, get_user_today_date, reset_week_offset, is_navigating, set_navigating

UNRESTRICTED_PAGE_ROUTES = ("/login", "/register")


def get_current_list_id() -> int | str | None:
    """Get current list ID from query parameters or storage."""
    try:
        # Check if context.client.page exists and has query attribute
        if not hasattr(context, 'client') or not hasattr(context.client, 'page') or not hasattr(context.client.page, 'query'):
            logger.warning("Cannot access page query parameters - context.client.page.query not available")
            # Fall back to storage
            stored_id = app.storage.user.get("current_list")
            logger.info(f"Using list ID from storage (no query available): {stored_id!r}")
            return stored_id
            
        # Get raw list parameter from URL
        list_param = context.client.page.query.get("list")
        logger.info(f"URL parameter 'list': {list_param!r} (type: {type(list_param)})")
        
        # Explicitly handle "None" case (case-insensitive)
        if list_param and list_param.lower() == "none":
            logger.info("'None' list selected (showing only habits with no list)")
            return "None"
        
        # If parameter exists but is empty, or parameter doesn't exist
        if list_param == "" or list_param is None:
            stored_id = app.storage.user.get("current_list")
            logger.info(f"No list parameter in URL, using from storage: {stored_id!r}")
            if stored_id:
                return stored_id
            
            logger.info("No list selected (showing all habits)")
            return None
        
        # Clean up list ID for integer values
        try:
            list_id = int(list_param.strip())
            logger.info(f"Using list ID from URL: {list_id}")
            
            # Store for persistence
            app.storage.user.update({"current_list": list_id})
            return list_id
        except ValueError:
            logger.warning(f"Invalid list ID format: {list_param!r}")
            return None
            
    except Exception as e:
        # Try storage as fallback for any errors
        logger.error(f"Error getting list ID: {str(e)}")
        stored_id = app.storage.user.get("current_list")
        logger.info(f"Using list ID from storage (fallback): {stored_id!r}")
        return stored_id


@ui.page("/gui/lists")
async def lists_page(user: User = Depends(current_active_user)) -> None:
    lists = await get_user_lists(user)
    await lists_page_ui(lists, user)


@ui.page("/gui")
@ui.page("/")
async def index_page(
    request: Request,
    user: User = Depends(current_active_user),
) -> None:
    # Reset to current week only if not navigating
    if not is_navigating():
        reset_week_offset()
    else:
        set_navigating(False)  # Clear navigation flag
    days = await get_display_days()
    
    # Extract list parameter directly from request
    list_param = request.query_params.get("list")
    logger.info(f"Index page - List parameter from request: {list_param!r}")
    
    # Store list ID for persistence if it's a valid integer
    if list_param and list_param.isdigit():
        list_id = int(list_param)
        app.storage.user.update({"current_list": list_id})
    
    # Handle different list parameter types (case-insensitive)
    current_list_id = None
    if list_param and list_param.lower() == "none":
        # For "None" (no list), get all habits and filter to show only those with no list
        habits = await get_user_habits(user)
        habits = [h for h in habits if h.list_id is None]
        current_list_id = "None"
        logger.info(f"Index page - Showing {len(habits)} habits with no list")
    elif list_param and list_param.isdigit():
        # For specific list ID, filter at database level
        list_id = int(list_param)
        habits = await get_user_habits(user, list_id)
        current_list_id = list_id
        logger.info(f"Index page - Showing {len(habits)} habits from list {list_id}")
    else:
        # Default case (no filter) or invalid list parameter
        habits = await get_user_habits(user)
        logger.info(f"Index page - Showing all {len(habits)} habits")
    
    # Pass the current list ID to the UI
    await index_page_ui(days, habits, user, current_list_id)


@ui.page("/gui/add")
async def add_page(user: User = Depends(current_active_user)) -> None:
    # Get all habits without filtering by list
    habits = await get_user_habits(user)
    await add_page_ui(habits, user)


@ui.page("/gui/order")
async def order_page(
    request: Request,
    user: User = Depends(current_active_user)
) -> None:
    # Extract list parameter directly from request
    list_param = request.query_params.get("list")
    logger.info(f"Order page - List parameter from request: {list_param!r}")
    
    # Store list ID for persistence if it's a valid integer
    if list_param and list_param.isdigit():
        list_id = int(list_param)
        app.storage.user.update({"current_list": list_id})
    
    # Handle different list parameter types (case-insensitive)
    current_list_id = None
    if list_param and list_param.lower() == "none":
        # For "None" (no list), get all habits and filter to show only those with no list
        habits = await get_user_habits(user)
        habits = [h for h in habits if h.list_id is None]
        current_list_id = "None"
        logger.info(f"Order page - Showing {len(habits)} habits with no list")
    elif list_param and list_param.isdigit():
        # For specific list ID, filter at database level
        list_id = int(list_param)
        habits = await get_user_habits(user, list_id)
        current_list_id = list_id
        logger.info(f"Order page - Showing {len(habits)} habits from list {list_id}")
    else:
        # Default case (no filter) or invalid list parameter
        habits = await get_user_habits(user)
        logger.info(f"Order page - Showing all {len(habits)} habits")
    
    # Pass the current list ID to the UI
    await order_page_ui(habits, user, current_list_id)


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
    habits = await get_user_habits(user)
    if not habits:
        ui.notify("No habits to export", color="negative")
        return
    await views.export_user_habits(habits, user.email)


@ui.page("/gui/import")
async def gui_import(user: User = Depends(current_active_user)) -> None:
    await import_ui_page(user)


@ui.page("/login")
async def login_page() -> Optional[RedirectResponse]:
    custom_header()
    if await views.is_gui_authenticated():
        return RedirectResponse("/gui")

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
        return RedirectResponse("/gui")

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
        favicon="statics/images/favicon.ico",
        dark=True,
    )
