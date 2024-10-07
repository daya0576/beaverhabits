from contextlib import contextmanager
import os

from nicegui import app, ui

from beaverhabits.app.auth import user_logout
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import compat_menu, menu_header, menu_icon_button
from beaverhabits.storage.meta import get_page_title, get_root_path


def custom_header():
    app.add_static_files("/images", "images")

    ui.add_head_html(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">'
    )
    ui.add_head_html('<meta name="apple-mobile-web-app-title" content="Beaver">')
    ui.add_head_html('<meta name="apple-mobile-web-app-capable" content="yes">')
    ui.add_head_html(
        '<meta name="apple-mobile-web-app-status-bar-style" content="black">'
    )
    ui.add_head_html('<meta name="theme-color" content="#121212">')

    # viewBox="90 90 220 220"
    ui.add_head_html(
        '<link rel="apple-touch-icon" href="/images/apple-touch-icon-v4.png">'
    )


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

        if not root_path.startswith("/demo"):
            compat_menu("Import", lambda: ui.open(os.path.join(root_path, "import")))
            ui.separator()

        compat_menu("Logout", lambda: user_logout() and ui.open("/login"))


@contextmanager
def layout(title: str | None = None, with_menu: bool = True):
    """Base layout for all pages."""
    root_path = get_root_path()
    title = title or get_page_title(root_path)
    with ui.column().classes("max-w-sm mx-auto sm:mx-0"):
        custom_header()

        with ui.row().classes("min-w-full"):
            menu_header(title, target=root_path)
            if with_menu:
                ui.space()
                with menu_icon_button(icons.MENU):
                    menu_component(root_path)

        yield
