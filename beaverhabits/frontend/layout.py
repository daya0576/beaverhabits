from contextlib import contextmanager
import os

from nicegui import ui

from beaverhabits.frontend.components import compat_menu, menu_icon_button


@contextmanager
def layout(root_path: str):
    with ui.column().classes("max-w-screen-lg"):
        with ui.row().classes("w-full"):
            ui.label("Habits").classes("text-semibold text-2xl")
            ui.space()
            # menu_icon_button("sym_r_add")
            with menu_icon_button("sym_r_menu"):
                with ui.menu():
                    compat_menu("Add", lambda: ui.open(os.path.join(root_path, "/add")))
                    compat_menu("Menu2", lambda: True)
                    ui.separator()
                    compat_menu("Logout", lambda: True)
        # ui.separator().style("background: hsla(0,0%,100%,.1)")

        yield
