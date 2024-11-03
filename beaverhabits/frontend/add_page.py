from nicegui import ui

from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitStarCheckbox,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList, HabitListBuilder, HabitStatus


@ui.refreshable
def add_ui(habit_list: HabitList):
    habits = HabitListBuilder(habit_list).status(HabitStatus.ACTIVE).build()

    for item in habits:
        with ui.grid(columns=8, rows=1).classes("w-full gap-0 items-center"):
            name = HabitNameInput(item)
            name.classes("col-span-6 break-all")

            star = HabitStarCheckbox(item, add_ui.refresh)
            star.props("flat fab-mini color=grey")
            star.classes("col-span-1")

            delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
            delete.props("flat fab-mini color=grey")
            delete.classes("col-span-1")


def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center"):
            add_ui(habit_list)

            with ui.grid(columns=9, rows=1).classes("w-full gap-0 items-center"):
                add = HabitAddButton(habit_list, add_ui.refresh)
                add.classes("col-span-7")
