from contextlib import contextmanager
import os

from nicegui import ui

from beaverhabits.frontend import icons
from beaverhabits.frontend.components import compat_menu, menu_header, menu_icon_button


@contextmanager
def layout(title: str, root_path: str):
    with ui.column().classes("max-w-sm mx-auto sm:mx-0"):
        with ui.row().classes("min-w-full"):
            menu_header(title, target=root_path)

            ui.space()

            with menu_icon_button(icons.MENU):
                with ui.menu():
                    compat_menu("Add", lambda: ui.open(os.path.join(root_path, "add")))
                    # compat_menu("Menu2", lambda: True)
                    ui.separator()
                    compat_menu("Logout", lambda: True)

        yield
