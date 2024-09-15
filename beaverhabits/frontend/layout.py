import os
from contextlib import contextmanager

from nicegui import ui

from beaverhabits.app.auth import user_logout
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import compat_menu, menu_header, menu_icon_button
from beaverhabits.storage.meta import get_page_title, get_root_path


def menu_component(root_path: str) -> None:
    """Dropdown menu for the top-right corner of the page."""
    with ui.menu():
        compat_menu("Add", lambda: ui.open(os.path.join(root_path, "add")))
        ui.separator()

        compat_menu(
            "Export",
            lambda: ui.open(os.path.join(root_path, "export"), new_tab=True),
        )
        ui.separator()

        compat_menu("Import", lambda: ui.open(os.path.join(root_path, "import")))
        ui.separator()

        compat_menu("Logout", lambda: user_logout() and ui.open("/login"))


@contextmanager
def layout(title: str | None = None):
    """Base layout for all pages."""
    root_path = get_root_path()
    title = title or get_page_title(root_path)
    with ui.column().classes("max-w-sm mx-auto sm:mx-0"):
        with ui.row().classes("min-w-full"):
            menu_header(title, target=root_path)
            ui.space()
            with menu_icon_button(icons.MENU):
                menu_component(root_path)

        yield
