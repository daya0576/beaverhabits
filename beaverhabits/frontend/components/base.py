from typing import Callable, Optional
from nicegui import ui
from nicegui.elements.button import Button

def link(text: str, target: str):
    return ui.link(text, target=target).classes(
        "dark:text-white  no-underline hover:no-underline"
    )

def menu_header(title: str, target: str):
    link = ui.link(title, target=target)
    link.classes(
        "text-semibold text-2xl dark:text-white no-underline hover:no-underline"
    )
    return link

def compat_menu(name: str, callback: Callable):
    return ui.menu_item(name, callback).props("dense").classes("items-center")

def menu_icon_button(
    icon_name: str, click: Optional[Callable] = None, tooltip: str | None = None
) -> Button:
    button_props = "flat=true unelevated=true padding=xs backgroup=none"
    button = ui.button(icon=icon_name, color=None, on_click=click).props(button_props)
    if tooltip:
        button = button.tooltip(tooltip)
    return button

def grid(columns: int, rows: int | None = 1) -> ui.grid:
    return ui.grid(columns=columns, rows=rows).classes("gap-0 items-center")
