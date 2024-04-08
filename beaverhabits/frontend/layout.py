from contextlib import contextmanager
import os

from nicegui import ui

from beaverhabits.frontend import icons
from beaverhabits.frontend.components import compat_menu, menu_icon_button


@contextmanager
def layout(root_path: str):
    with ui.column():
        with ui.row().classes("w-full"):
            link = ui.link("Habits", target=root_path)
            ui.colors()
            link.classes(
                "text-semibold text-2xl dark:text-white no-underline hover:no-underline"
            )

            ui.space()
            # menu_icon_button("sym_r_add")
            with menu_icon_button(icons.MENU):
                with ui.menu():
                    compat_menu("Add", lambda: ui.open(os.path.join(root_path, "add")))
                    # compat_menu("Menu2", lambda: True)
                    ui.separator()
                    compat_menu("Logout", lambda: True)

        with ui.column().classes("w-full"):
            yield
