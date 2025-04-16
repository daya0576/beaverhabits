from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Request
from nicegui import ui, context, app

from beaverhabits.app.crud import get_user_lists
from beaverhabits.configs import settings
import datetime
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import menu_header, menu_icon_button
from beaverhabits.frontend.components.index import week_navigation # Added import
from beaverhabits.logging import logger

from .header import add_meta_tags, add_analytics, add_all_scripts
from .menu import list_selector, menu_component
from .utils import get_page_title

@asynccontextmanager
async def layout(
    title: str | None = None, 
    with_menu: bool = True, 
    user=None, 
    current_list_id: str | int | None = None,
    days: list[datetime.date] | None = None # Added days parameter
):
    """Base layout for all pages."""
    title = title or "Beaver Habits"

    with ui.column().classes("w-full") as c:
        # Standard headers and scripts
        add_meta_tags()
        #add_analytics()
        add_all_scripts()

        path = context.client.page.path
        logger.info(f"Rendering page: {path}")
        
        # Use justify-between, wrap elements in rows for proper spacing
        with ui.row().classes("w-full items-center justify-between pt-2 pr-2"): 
            # --- Left Element ---
            left_container = ui.row().classes("items-center") 
            with left_container:
                # Show title on all pages except main /gui page
                if path != settings.GUI_MOUNT_PATH:
                    page_title = get_page_title(path, title)
                    menu_header(page_title, target=settings.GUI_MOUNT_PATH)
                
                # Add list selector if not on lists, add, or order pages AND on main page
                # (Title takes precedence on other pages based on above logic)
                elif not any(x in path for x in ["/lists", "/add", "/order"]) and user:
                    lists = await get_user_lists(user)
                    
                    # If no list ID provided, try to get from query string or storage
                    if current_list_id is None:
                        try:
                            # Try to get list parameter from page query
                            if hasattr(context.client.page, 'query'):
                                list_param = context.client.page.query.get("list")
                                logger.info(f"Layout - List parameter from page query: {list_param!r}")
                                
                                # Convert to appropriate type (case-insensitive)
                                if list_param and list_param.lower() == "none":
                                    current_list_id = "None"
                                    logger.info("Layout - Using 'None' string value from URL")
                                elif list_param and list_param.isdigit():
                                    current_list_id = int(list_param)
                                    logger.info(f"Layout - Using list ID {current_list_id} from URL")
                                    # Store for persistence
                                    app.storage.user.update({"current_list": current_list_id})
                                else:
                                    # Fall back to storage if no valid parameter
                                    current_list_id = app.storage.user.get("current_list")
                                    logger.info(f"Layout - Using list from storage: {current_list_id!r}")
                            else:
                                # Fall back to storage if query not available
                                current_list_id = app.storage.user.get("current_list")
                                logger.info(f"Layout - Using list from storage (no query available): {current_list_id!r}")
                        except Exception as e:
                            logger.error(f"Layout - Error getting list parameter: {e}")
                            # Fall back to centralized function
                            from beaverhabits.routes import get_current_list_id
                            current_list_id = get_current_list_id()
                            logger.info(f"Layout - Using list from centralized function: {current_list_id!r}")
                    else:
                        logger.info(f"Layout - Using provided list ID: {current_list_id!r}")
                    
                    # Debug list data
                    logger.debug(f"Layout - Available lists: {[(l.id, l.name) for l in lists]}")
                    logger.debug(f"Layout - Current list value: {current_list_id!r} (type: {type(current_list_id)})")
                    
                    await list_selector(lists, current_list_id, path)
                # else: Left container remains empty on index page if no user/lists

            # --- Center Element (grows and centers content) ---
            center_container = ui.row().classes("items-center justify-center flex-grow")
            with center_container:
                # Add week navigation only on the main page and if days are provided
                if path == settings.GUI_MOUNT_PATH and days:
                    await week_navigation(days)
                    # Removed ui.space() from here

            # --- Right Element ---
            right_container = ui.row().classes("items-center")
            with right_container:
                if with_menu:
                    with menu_icon_button(icons.MENU):
                        menu_component()

        yield
