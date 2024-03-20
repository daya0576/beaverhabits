from typing import Callable
from nicegui import ui
from nicegui.elements.checkbox import Checkbox

from beaverhabits.view import HabitList
from beaverhabits.utils import dummy_days


HABIT_LIST_RECORD_COUNT = 5


def build_check_box(value: bool, on_change: Callable, dense: bool = False) -> Checkbox:
    checkbox = ui.checkbox(value=value, on_change=on_change)

    checkbox.props('checked-icon="r_check" unchecked-icon="r_close" keep-color')
    if not value:
        checkbox.props("color=grey-8")
    if dense:
        checkbox.props("dense")

    return checkbox


@ui.refreshable
def habit_list_ui(habits: HabitList):
    if not habits.items:
        ui.label("List is empty.").classes("mx-auto")
        return

    with ui.column().classes("gap-1.5"):
        # compat card
        row_compat_classes = "pl-4 pr-1 py-0"
        compat_card = (
            lambda: ui.card().classes(row_compat_classes).classes("shadow-none")
        )

        # grid: 5 | 2 2 2 2 2
        grid_classes = "w-full gap-0 items-center"
        grid = lambda rows: ui.grid(columns=15, rows=rows).classes(grid_classes)
        left_classes, right_classes = (
            "col-span-5 break-all",
            "col-span-2 px-1.5 justify-self-center",
        )

        # header
        with grid(2).classes(row_compat_classes):
            for fmt in ("%a", "%d"):
                ui.label("").classes(left_classes)
                for date in dummy_days(HABIT_LIST_RECORD_COUNT):
                    label = ui.label(str(date.strftime(fmt))).classes(right_classes)
                    label.style("color: #9e9e9e; font-size: 85%; font-weight: 500")

        # body
        for habit in habits.items:
            with compat_card():
                with grid(1):
                    ui.label(habit.name).classes(left_classes)
                    for record in habit.records:
                        checkbox = build_check_box(
                            value=record.done, on_change=habit_list_ui.refresh
                        )
                        checkbox.bind_value(record, "done")
                        checkbox.classes(right_classes)


def index_page_ui(habits: HabitList):
    with ui.column().classes("max-w-screen-lg"):
        ui.label("Habits").classes("text-semibold text-2xl")
        # ui.separator().props("color=grey-8 ")
        habit_list_ui(habits)
