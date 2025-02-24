from contextlib import asynccontextmanager
from typing import Optional

from nicegui import ui, context

from beaverhabits.app.crud import get_user_lists
from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import menu_header, menu_icon_button
from beaverhabits.logging import logger

from .header import add_meta_tags, add_analytics, add_all_scripts
from .menu import list_selector, menu_component
from .utils import get_page_title

@asynccontextmanager
async def layout(title: str | None = None, with_menu: bool = True, user=None):
    """Base layout for all pages."""
    title = title or "Beaver Habits"

    with ui.column().classes("w-full") as c:
        # Standard headers and scripts
        add_meta_tags()
        #add_analytics()
        add_all_scripts()

        path = context.client.page.path
        logger.info(f"Rendering page: {path}")
        
        with ui.row().classes("w-full items-center justify-between pt-2 pr-2"):
            # Show title on all pages except main /gui page
            if path != settings.GUI_MOUNT_PATH:
                page_title = get_page_title(path, title)
                menu_header(page_title, target=settings.GUI_MOUNT_PATH)
            
            # Add list selector if not on lists, add, or order pages
            if not any(x in path for x in ["/lists", "/add", "/order"]) and user:
                lists = await get_user_lists(user)
                # Get current list ID using the centralized function
                from beaverhabits.routes import get_current_list_id
                current_list = get_current_list_id()
                
                # Debug list data
                logger.debug(f"Layout - Available lists: {[(l.id, l.name) for l in lists]}")
                logger.debug(f"Layout - Current list value: {current_list!r} (type: {type(current_list)})")
                
                await list_selector(lists, current_list, path)
            else:
                ui.space()  # Empty space on the left when no list selector
                
            if with_menu:
                with menu_icon_button(icons.MENU):
                    menu_component()

        yield
