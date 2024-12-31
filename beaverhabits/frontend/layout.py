import os
from contextlib import contextmanager

from nicegui import context, ui

from beaverhabits.app.auth import user_logout
from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import compat_menu, menu_header, menu_icon_button
from beaverhabits.logging import logger
from beaverhabits.storage.meta import get_page_title, get_root_path


def redirect(x):
    ui.navigate.to(os.path.join(get_root_path(), x))


def open_tab(x):
    ui.navigate.to(os.path.join(get_root_path(), x), new_tab=True)


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


def menu_component(root_path: str) -> None:
    """Dropdown menu for the top-right corner of the page."""
    with ui.menu():
        compat_menu("Add", lambda: redirect("add"))
        ui.separator()
        # compat_menu("Edit", lambda: redirect("order"))
        # ui.separator()

        compat_menu("Export", lambda: open_tab("export"))
        ui.separator()

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
        add_umami_headers()

        path = context.client.page.path
        logger.info(f"Rendering page: {path}")
        with ui.row().classes("min-w-full gap-x-0"):
            menu_header(title, target=root_path)
            if with_menu:
                ui.space()
                if "order" in path:
                    menu_icon_button(icons.ADD, click=lambda: redirect("add"), tooltip="Add Habits")
                if "add" in path:
                    menu_icon_button("drag_indicator", click=lambda: redirect("order"), tooltip="Reorder habits")
                with menu_icon_button(icons.MENU):
                    menu_component(root_path)

        yield
