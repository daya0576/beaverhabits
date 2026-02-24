from itertools import chain

from nicegui import ui

from beaverhabits.frontend import components
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitStarCheckbox,
    habits_by_tags,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList, HabitListBuilder, HabitStatus


@ui.refreshable
def add_ui(habit_list: HabitList):
    habits = HabitListBuilder(habit_list).status(HabitStatus.ACTIVE).build()
    groups = habits_by_tags(habits)
    for item in chain.from_iterable(groups.values()):
        with components.grid(columns=10).props("role=listitem"):
            with HabitNameInput(item, refresh=add_ui.refresh) as name:
                name.classes("col-span-8 break-all")
                name.props(
                    'aria-label="Habit name" aria-description="press enter to save"'
                )

            star = HabitStarCheckbox(item, add_ui.refresh)
            star.classes("col-span-1")
            star.props('aria-label="Star habit" aria-description="move to top of list"')

            delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
            delete.classes("col-span-1")
            delete.props('aria-label="Delete habit"')


def add_page_ui(habit_list: HabitList):
    with layout(habit_list=habit_list):
        with ui.column().classes("items-center w-full").props("role=list"):
            add_ui(habit_list)

        with ui.grid(columns=10, rows=1).classes("w-full gap-0 items-center"):
            add = HabitAddButton(habit_list, add_ui.refresh)
            add.classes("col-span-8")
        ui.button("Save").props("flat").on_click(
            lambda: ui.navigate.to("/gui")
        )
