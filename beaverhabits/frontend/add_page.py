from beaverhabits.frontend import components
from nicegui import ui

from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList
from beaverhabits.logging import logger

grid_classes = "w-full gap-0 items-center"


async def item_drop(e, habit_list: HabitList):
    # Move element
    elements = ui.context.client.elements
    dragged = elements[int(e.args["id"][1:])]
    dragged.move(target_index=e.args["new_index"])

    # Update habit order
    assert dragged.parent_slot is not None
    habits = [
        x.habit
        for x in dragged.parent_slot.children
        if isinstance(x, components.HabitAddCard)
    ]
    habit_list.order = [str(x.id) for x in habits]
    logger.info(f"New order: {habits}")


@ui.refreshable
def add_ui(habit_list: HabitList):
    for item in habit_list.habits:
        with components.HabitAddCard(item):
            with ui.row().classes("items-center"):
                name = HabitNameInput(item)
                name.classes("flex-grow")

                delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
                delete.props("flat fab-mini color=grey")


def add_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center").classes("sortable"):
            add_ui(habit_list)

        with ui.card().classes("w-full").props("flat"):
            with ui.grid(columns=9, rows=1).classes("w-full gap-0 items-center"):
                add = HabitAddButton(habit_list, add_ui.refresh)
                add.classes("col-span-7")

    ui.add_body_html(
        r"""
        <script type="module">
        import '/statics/libs/sortable.min.js';
        document.addEventListener('DOMContentLoaded', () => {
            Sortable.create(document.querySelector('.sortable'), {
                animation: 150,
                ghostClass: 'opacity-50',
                onEnd: (evt) => emitEvent("item_drop", {id: evt.item.id, new_index: evt.newIndex }),
            });
        });
        </script>
    """
    )
    ui.on("item_drop", lambda e: item_drop(e, habit_list))
