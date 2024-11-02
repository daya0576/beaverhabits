from nicegui import ui

from beaverhabits.frontend import components
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.logging import logger
from beaverhabits.storage.storage import HabitList, HabitStatus


async def item_drop(e, habit_list: HabitList):
    new_index = e.args["new_index"]
    logger.info(f"Item drop: {e.args['id']} -> {new_index}")

    # Move element
    elements = ui.context.client.elements
    dragged = elements[int(e.args["id"][1:])]
    dragged.move(target_index=e.args["new_index"])

    # Update habit order
    assert dragged.parent_slot is not None
    habits = [
        x.habit
        for x in dragged.parent_slot.children
        if isinstance(x, components.HabitOrderCard) and x.habit
    ]

    # Unarchive dragged habit
    if new_index < len(habits) - 1:
        if habits[new_index + 1].status == HabitStatus.ACTIVE:
            habits[new_index].status = HabitStatus.ACTIVE
    # Archive dragged Habit
    if new_index > 1:
        if habits[new_index - 1].status == HabitStatus.ARCHIVED:
            habits[new_index].status = HabitStatus.ARCHIVED

    habit_list.order = [str(x.id) for x in habits]
    logger.info(f"New order: {habits}")

    add_ui.refresh()


@ui.refreshable
def add_ui(habit_list: HabitList):
    for item in habit_list.habits:
        with components.HabitOrderCard(item):
            with ui.grid(columns=12, rows=1).classes("gap-0 items-center"):
                if item.status == HabitStatus.ACTIVE:
                    name = HabitNameInput(item)
                    name.props("borderless")
                else:
                    name = ui.label(item.name)
                name.classes("col-span-4 col-3")

                ui.space().classes("col-span-7")

                delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
                delete.classes("col-span-1")


def order_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("w-full pl-1 items-center gap-3"):
            with ui.column().classes("sortable").classes("gap-3"):
                add_ui(habit_list)

            with components.HabitOrderCard():
                with ui.grid(columns=12, rows=1).classes("gap-0 items-center"):
                    add = HabitAddButton(habit_list, add_ui.refresh)
                    add.classes("col-span-12")
                    add.props("borderless")

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
