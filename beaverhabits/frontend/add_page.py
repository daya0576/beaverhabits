from nicegui import events, ui
from beaverhabits.frontend.components import HabitPrioritySelect
from beaverhabits.frontend.layout import layout

from beaverhabits.storage.storage import HabitList

PRIORITIES = {1: "P1", 2: "P2", 3: "P3", 4: "P4"}


@ui.refreshable
def add_ui(habit_list: HabitList):
    habit_list = habit_list
    for item in habit_list.items:
        with ui.row().classes("items-center"):
            ui.input(value=item.name).classes("flex-grow").bind_value(
                item, "name"
            ).props("dense filled")

            select = HabitPrioritySelect(item, habit_list, PRIORITIES, item.priority)
            select.props("dense")

            ui.button(
                on_click=lambda item=item: habit_list.remove(item), icon="delete"
            ).props("flat fab-mini color=grey")


def add_page_ui(habit_list: HabitList, root_path: str):
    with layout(root_path):
        add_ui(habit_list)
        add_input = ui.input("New item").props("dense")
        add_input.on(
            "keydown.enter",
            lambda: (habit_list.add(add_input.value), add_input.set_value("")),
        )
