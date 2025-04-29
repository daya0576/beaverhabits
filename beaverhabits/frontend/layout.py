from contextlib import contextmanager

from nicegui import context, ui

from beaverhabits.app.auth import user_logout
from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import (
    habit_edit_dialog,
    menu_header,
    menu_icon_button,
    menu_icon_item,
    open_tab,
    redirect,
)
from beaverhabits.frontend.menu import add_menu, sort_menu
from beaverhabits.logger import logger
from beaverhabits.storage.meta import (
    get_page_title,
    get_root_path,
    is_page_demo,
)
from beaverhabits.storage.storage import Habit, HabitList


def custom_headers():
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
    if settings.UMAMI_ANALYTICS_ID:
        ui.add_head_html(
            f'<script defer src="https://cloud.umami.is/script.js" data-website-id="{settings.UMAMI_ANALYTICS_ID}"></script>'
        )


def separator():
    ui.separator().props('aria-hidden="true"')


@ui.refreshable
def menu_component(habit: Habit | None = None, habit_list: HabitList | None = None):
    """Dropdown menu for the top-right corner of the page."""
    edit_dialog = habit_edit_dialog(habit) if habit else ui.dialog()
    path = context.client.page.path

    with ui.menu().props('role="menu"'):
        # habit page
        if habit:
            edit = menu_icon_item("Edit", on_click=edit_dialog.open)
            edit.props('aria-label="Edit habit"')
            separator()
            add_menu()
            separator()
        if habit_list:
            sort_menu(habit_list) if "add" in path else add_menu()
            separator()

        # Export & import
        if habit_list:
            menu_icon_item("Export", lambda: redirect("export"))
            separator()
            imp = menu_icon_item("Import", lambda: redirect("import"))
            if is_page_demo():
                imp.classes("disabled")
            separator()

        # Login & Logout
        if is_page_demo():
            menu_icon_item("Login", lambda: ui.navigate.to("/login"))
        else:
            menu_icon_item("Logout", lambda: user_logout() and ui.navigate.to("/login"))

    # Prevent white flash on page load
    ui.add_css("body { background-color: #121212; color: white;  }")


@contextmanager
def layout(
    title: str | None = None,
    habit: Habit | None = None,
    habit_list: HabitList | None = None,
):
    """Base layout for all pages."""
    # Center the content on small screens
    with ui.column().classes("mx-auto mx-0"):
        # Standard headers
        custom_headers()

        # Layout wrapper
        with ui.row().classes("min-w-full gap-x-1"):
            title, target = title or get_page_title(), get_root_path()
            menu_header(title, target=target)
            ui.space()
            with menu_icon_button(icons.MENU):
                menu_component(habit, habit_list)

        yield
