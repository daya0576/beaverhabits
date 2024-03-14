from typing import Callable

from nicegui import ui
from nicegui.elements.checkbox import Checkbox


def build_check_box(value: bool, on_change: Callable, dense: bool = False) -> Checkbox:
    checkbox = ui.checkbox(value=value, on_change=on_change)

    checkbox.props('checked-icon="r_check" unchecked-icon="r_close" keep-color')
    if not value:
        checkbox.props("color=grey-8")
    if dense:
        checkbox.props("dense")

    return checkbox
