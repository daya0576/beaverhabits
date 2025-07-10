from contextlib import contextmanager

from nicegui import background_tasks, ui

from beaverhabits import views
from beaverhabits.app.auth import user_logout
from beaverhabits.configs import settings
from beaverhabits.frontend import css
from beaverhabits.frontend.components import (
    habit_edit_dialog,
    menu_header,
    menu_icon_button,
    menu_icon_item,
    redirect,
    separator,
)
from beaverhabits.frontend.menu import add_menu, sort_menu
from beaverhabits.storage.meta import (
    get_root_path,
    is_page_demo,
    page_path,
    page_title,
)
from beaverhabits.storage.storage import Habit, HabitList
from beaverhabits.utils import fetch_user_dark_mode


def pwa_headers():
    # Apple touch icon
    ui.add_head_html(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">'
    )
    ui.add_head_html('<meta name="apple-mobile-web-app-title" content="Beaver">')
    ui.add_head_html(
        '<meta name="apple-mobile-web-app-status-bar-style" content="black">'
    )
    # viewBox="90 90 220 220"
    ui.add_head_html(
        '<link rel="apple-touch-icon" href="/statics/images/apple-touch-icon-v4.png">'
    )

    # PWA support
    ui.add_head_html('<link rel="manifest" href="/statics/pwa/manifest.json">')

    # Extend background to iOS notch
    ui.add_head_html(
        """
        <meta name="theme-color" content="#F9F9F9" media="(prefers-color-scheme: light)" />
        <meta name="theme-color" content="#121212" media="(prefers-color-scheme: dark)" />
        """
    )

    # Experimental iOS standalone mode
    if settings.ENABLE_IOS_STANDALONE:
        ui.add_head_html('<meta name="mobile-web-app-capable" content="yes">')


def custom_headers():
    # SEO meta tags
    ui.add_head_html(
        '<meta name="description" content="A self-hosted habit tracking app without "Goals"">'
    )

    # Analytics
    if settings.UMAMI_ANALYTICS_ID:
        ui.add_head_html(
            f'<script defer src="https://cloud.umami.is/script.js" data-website-id="{settings.UMAMI_ANALYTICS_ID}"></script>'
        )

    # Long-press event
    ui.add_head_html('<script src="/statics/libs/long-press-event.min.js"></script>')

    # Prevent white flash on page load
    ui.add_css(css.WHITE_FLASH_PREVENT)


@ui.refreshable
def menu_component():
    """Dropdown menu for the top-right corner of the page."""
    with ui.menu().props('role="menu" transition-duration="50"'):
        add_menu()
        separator()

        # Export & import
        menu_icon_item("Export", lambda: redirect("export"))
        separator()
        imp = menu_icon_item("Import", lambda: redirect("import"))
        if is_page_demo():
            imp.classes("disabled")
        separator()

        # Login & Logout
        menu_icon_item("Logout", lambda: user_logout() and ui.navigate.to("/login"))


@contextmanager
def layout(
    title: str | None = None,
    habit: Habit | None = None,
    habit_list: HabitList | None = None,
):
    # Standard headers
    custom_headers()
    pwa_headers()

    # Center the content on small screens
    with ui.column().classes("mx-auto mx-0"):

        # Layout wrapper
        with ui.row().classes("w-full gap-x-1"):
            title, target = title or page_title(), get_root_path()
            menu_header(title, target=target)
            ui.space()

            if habit:
                edit_dialog = habit_edit_dialog(habit)
                edit_btn = menu_icon_button("sym_r_pen_size_3", tooltip="Edit habit")
                edit_btn.on_click(edit_dialog.open)
            elif habit_list and "add" in page_path():
                with menu_icon_button("sym_o_swap_vert", tooltip="Sort"):
                    sort_menu(habit_list)

            with menu_icon_button("sym_o_menu"):
                menu_component()

        yield
