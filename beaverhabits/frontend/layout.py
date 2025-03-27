import os
from contextlib import contextmanager

from nicegui import app, context, ui

from beaverhabits.app.auth import user_logout
from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import (
    compat_menu,
    menu_header,
    menu_icon_button,
    nav_loading,
)
from beaverhabits.logging import logger
from beaverhabits.storage.meta import (
    get_page_title,
    get_root_path,
    is_page_demo,
)


def redirect(x):
    ui.navigate.to(os.path.join(get_root_path(), x))


def open_tab(x):
    ui.navigate.to(os.path.join(get_root_path(), x), new_tab=True)


def custom_header():
    # Apple touch icon
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

    # PWA support
    ui.add_head_html('<link rel="manifest" href="/statics/pwa/manifest.json">')

    # Experimental iOS standalone mode
    if settings.ENABLE_IOS_STANDALONE:
        ui.add_head_html('<meta name="mobile-web-app-capable" content="yes">')

    # SEO meta tags
    ui.add_head_html(
        '<meta name="description" content="A self-hosted habit tracking app without "Goals"">'
    )


def add_umami_headers():
    ui.add_head_html(
        '<script defer src="https://cloud.umami.is/script.js" data-website-id="246fa4ac-0f4f-464a-8a32-14c9f75fed77"></script>'
    )


def separator():
    ui.separator().props('aria-hidden="true"')


def menu_component() -> None:
    """Dropdown menu for the top-right corner of the page."""
    with ui.menu().props('role="menu"'):
        path = context.client.page.path
        if "add" in path:
            compat_menu("Reorder", lambda: redirect("order"))
        else:
            add = compat_menu("Add", lambda: redirect("add"))
            add.props('aria-label="Edit habit list"')
        separator()

        compat_menu("Export", lambda: open_tab("export"))
        separator()
        imp = compat_menu("Import", lambda: redirect("import"))
        separator()
        if is_page_demo():
            imp.classes("disabled")

        if is_page_demo():
            compat_menu("Login", lambda: ui.navigate.to("/login"))
        else:
            compat_menu("Logout", lambda: user_logout() and ui.navigate.to("/login"))


def pre_cache():
    # lazy load echart: https://github.com/zauberzeug/nicegui/discussions/1452
    # hash: nicegui.dependencies.compute_key
    # ui.context.client.on_connect(javascript.load_cache)
    ui.add_css("body { background-color: #121212; color: white;  }")


@contextmanager
def layout(title: str | None = None, with_menu: bool = True):
    """Base layout for all pages."""
    title = title or get_page_title()

    with ui.column() as c:
        # Standard headers
        custom_header()
        add_umami_headers()
        pre_cache()

        # Center the content on small screens
        c.classes("mx-auto")
        if not settings.ENABLE_DESKTOP_ALGIN_CENTER:
            c.classes("sm:mx-0")

        path = context.client.page.path
        logger.info(f"Rendering page: {path}")
        with ui.row().classes("min-w-full gap-x-0"):
            menu_header(title, target=get_root_path())
            if with_menu:
                ui.space()
                # overlay blur
                nav_loading()
                with menu_icon_button(icons.MENU):
                    menu_component()

        yield
