from typing import Callable, Optional
from nicegui import ui
from nicegui.elements.button import Button
from nicegui.elements.checkbox import Checkbox


def compat_menu(name: str, callback: Callable):
    return ui.menu_item(name, callback).classes("items-center")


def menu_icon_button(icon_name: str, click: Optional[Callable] = None) -> Button:
    button_props = "flat=true unelevated=true padding=xs backgroup=none"
    return ui.button(icon=icon_name, color=None).props(button_props)


def menu_more_button(icon_name: str):
    with menu_icon_button(icon_name):
        with ui.menu():
            compat_menu("Menu1", lambda: True)
            compat_menu("Menu2", lambda: True)
            ui.separator()
            compat_menu("Logout", lambda: True)


def habit_check_box(value: bool, on_change: Callable, dense: bool = False) -> Checkbox:
    checkbox = ui.checkbox(value=value, on_change=on_change)

    checkbox.props(f'checked-icon="sym_r_done" unchecked-icon="sym_r_close" keep-color')
    if not value:
        checkbox.props("color=grey-8")
    if dense:
        checkbox.props("dense")

    return checkbox
