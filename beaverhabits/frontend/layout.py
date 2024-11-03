from contextlib import contextmanager
import os

from beaverhabits.app.auth import user_logout
from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import compat_menu, menu_header, menu_icon_button
from beaverhabits.storage.meta import get_page_title, get_root_path
from nicegui import ui


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


def menu_component(root_path: str) -> None:
    """Dropdown menu for the top-right corner of the page."""

    def redirect(x):
        ui.navigate.to(os.path.join(root_path, x))

    def open_tab(x):
        ui.navigate.to(os.path.join(root_path, x), new_tab=True)

    with ui.menu():
        compat_menu("Add", lambda: redirect("add"))
        compat_menu("Sort", lambda: redirect("order"))
        ui.separator()

        compat_menu("Export", lambda: open_tab("export"))
        if not root_path.startswith("/demo"):
            compat_menu("Import", lambda: redirect("import"))
            ui.separator()

        compat_menu("Logout", lambda: user_logout() and ui.navigate.to("/login"))


@contextmanager
def layout(title: str | None = None, with_menu: bool = True):
    """Base layout for all pages."""
    root_path = get_root_path()
    title = title or get_page_title(root_path)

    with ui.column() as c:
        # Center the content on small screens
        c.classes("max-w-sm mx-auto")
        if not settings.ENABLE_DESKTOP_ALGIN_CENTER:
            c.classes("sm:mx-0")

        # Standard headers
        custom_header()

        with ui.row().classes("min-w-full"):
            menu_header(title, target=root_path)
            if with_menu:
                ui.space()
                with menu_icon_button(icons.MENU):
                    menu_component(root_path)

        yield
