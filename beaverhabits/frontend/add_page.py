from nicegui import ui
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitPrioritySelect,
)
from beaverhabits.frontend.layout import layout

from beaverhabits.storage.storage import HabitList, Priority


PRIORITIES = {
    1: Priority.P1.name,
    2: Priority.P2.name,
    3: Priority.P3.name,
    4: Priority.P4.name,
    100: "  ",
}


@ui.refreshable
def add_ui(habit_list: HabitList):
    habit_list = habit_list
    for item in habit_list.habits:
        with ui.row().classes("items-center gap-0"):
            name = HabitNameInput(item)
            name.props("dense").classes("flex-grow")

            priority = HabitPrioritySelect(item, habit_list, PRIORITIES, add_ui.refresh)
            priority.props("dense")

            delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
            delete.props("flat fab-mini color=grey")


def add_page_ui(habit_list: HabitList, root_path: str):
    with layout(root_path):
        add_ui(habit_list)

    add = HabitAddButton(habit_list, add_ui.refresh)
    add.props("dense")
