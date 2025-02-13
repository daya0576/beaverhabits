import os
from contextlib import asynccontextmanager

from typing import List as TypeList

from nicegui import app, context, ui

from beaverhabits import views
from beaverhabits.storage.storage import List, Habit

from beaverhabits.app.auth import user_logout
from beaverhabits.configs import settings
from beaverhabits.frontend import icons, css
from beaverhabits.frontend.components import compat_menu, menu_header, menu_icon_button
from beaverhabits.logging import logger
from beaverhabits.storage.meta import get_page_title, get_root_path, is_demo


def redirect(x):
    ui.navigate.to(os.path.join(get_root_path(), x))


def open_tab(x):
    ui.navigate.to(os.path.join(get_root_path(), x), new_tab=True)


def add_page_scripts():
    """Add JavaScript and CSS to the page."""
    # Add settings as JavaScript variables
    ui.add_head_html(f'''
        <script>
        window.HABIT_SETTINGS = {{
            colors: {{
                skipped: "{settings.HABIT_COLOR_SKIPPED}",
                completed: "{settings.HABIT_COLOR_COMPLETED}",
                incomplete: "{settings.HABIT_COLOR_INCOMPLETE}"
            }}
        }};
        </script>
    ''')
    
    # Add JavaScript files
    from beaverhabits.frontend.javascript import js_paths
    for js_file in js_paths.values():
        ui.add_head_html(f'<script src="{js_file}"></script>')
    
    # Add CSS for animations
    ui.add_head_html(f'<style>{css.habit_animations}</style>')
    # Add CSS for transitions
    ui.add_head_html('''
        <style>
        .habit-card {
            transition: transform 0.3s ease-out;
        }
        .resort-pending {
            position: relative;
        }
        .resort-pending::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: #4CAF50;
            animation: progress 2s linear;
        }
        @keyframes progress {
            0% { width: 100%; }
            100% { width: 0%; }
        }
        .highlight-card {
            animation: highlight 1s ease-out;
        }
        @keyframes highlight {
            0% { background-color: rgba(76, 175, 80, 0.2); }
            100% { background-color: transparent; }
        }
        </style>
    ''')

def custom_header():
    ui.add_head_html(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">'
    )
    ui.add_head_html('<meta name="apple-mobile-web-app-title" content="Beaver">')
    ui.add_head_html(
        '<meta name="apple-mobile-web-app-status-bar-style" content="black">'
    )
    ui.add_head_html('<meta name="theme-color" content="#121212">')

    # viewBox="90 90 220 220"
    ui.add_head_html(
        '<link rel="apple-touch-icon" href="/statics/images/apple-touch-icon-v4.png">'
    )

    # Experimental PWA support
    if settings.ENABLE_IOS_STANDALONE:
        ui.add_head_html('<meta name="apple-mobile-web-app-capable" content="yes">')


def add_umami_headers():
    ui.add_head_html(
        '<script defer src="https://cloud.umami.is/script.js" data-website-id="246fa4ac-0f4f-464a-8a32-14c9f75fed77"></script>'
    )


@ui.refreshable
async def list_selector(lists: TypeList[List[Habit]], current_list_id: str | None = None, path: str = ""):
    """Dropdown for selecting current list."""
    with ui.row().classes("items-center gap-2"):
        # Dropdown for list selection
        # Create name-to-id mapping
        name_to_id = {"No List": None}
        name_to_id.update({list.name: list.id for list in lists})
        
        # Create options list
        options = list(name_to_id.keys())
        
        # Get current list ID from storage or URL
        stored_list_id = app.storage.user.get("current_list")
        current_list_id = current_list_id or stored_list_id
        
        # Find current name from ID
        current_name = next(
            (name for name, id in name_to_id.items() if id == current_list_id),
            "No List"
        )
        
        # Log debug info
        logger.debug(f"List options: {options}")
        logger.debug(f"Current list ID: {current_list_id}")
        logger.debug(f"Current name: {current_name}")
        
        ui.select(
            options=options,
            value=current_name,
            on_change=lambda e: (
                app.storage.user.update({"current_list": name_to_id[e.value]}),
                # Update URL without navigation on add page
                # Update URL based on page type
                ui.navigate.to(
                    # For add page: update current path with list parameter
                    f"{path}?list={name_to_id[e.value]}" if path.endswith("/add") and name_to_id[e.value] else
                    # For add page with no list: keep current path
                    path if path.endswith("/add") else
                    # For main page: navigate to root with list parameter
                    f"{get_root_path()}?list={name_to_id[e.value]}" if name_to_id[e.value] else
                    # For main page with no list: navigate to root
                    get_root_path()
                )
            )
        ).props('outlined dense options-dense')
        
        # Add list button
        ui.button(icon=icons.ADD, on_click=lambda: redirect("lists")).props("flat dense")


def menu_component() -> None:
    """Dropdown menu for the top-right corner of the page."""
    with ui.menu():
        show_import = not is_demo()
        show_export = True

        path = context.client.page.path
        if "add" in path:
            compat_menu("Reorder", lambda: redirect("order"))
        else:
            compat_menu("Add", lambda: redirect("add"))
        ui.separator()

        compat_menu("Lists", lambda: redirect("lists"))
        ui.separator()

        if show_export:
            compat_menu("Export", lambda: open_tab("export"))
            ui.separator()
        if show_import:
            compat_menu("Import", lambda: redirect("import"))
            ui.separator()

        compat_menu("Logout", lambda: user_logout() and ui.navigate.to("/login"))


@asynccontextmanager
async def layout(title: str | None = None, with_menu: bool = True, user=None):
    """Base layout for all pages."""

    root_path = get_root_path()
    title = title or get_page_title(root_path)

    with ui.column() as c:
        # Center the content on small screens
        c.classes("mx-auto")
        if not settings.ENABLE_DESKTOP_ALGIN_CENTER:
            c.classes("sm:mx-0")

        # Standard headers and scripts
        custom_header()
        add_umami_headers()
        add_page_scripts()

        path = context.client.page.path
        logger.info(f"Rendering page: {path}")
        with ui.row().classes("min-w-full gap-x-0 items-center"):
            menu_header(title, target=root_path)
            
            # Add list selector if not on lists or add page
            if not path.endswith("/lists") and user:
                ui.space()
                lists = await views.get_user_lists(user)
                try:
                    current_list = context.client.page.query.get("list", "")
                    # Handle "None" string from URL
                    current_list = None if current_list == "None" else current_list
                except AttributeError:
                    current_list = None
                await list_selector(lists, current_list, path)
                
                ui.space()
            if with_menu:
                with menu_icon_button(icons.MENU):
                    menu_component()

        yield
