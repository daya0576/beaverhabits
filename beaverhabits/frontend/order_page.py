from nicegui import ui

from beaverhabits.frontend import components
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.logging import logger
from beaverhabits.storage.storage import HabitList, HabitListBuilder, HabitStatus


async def item_drop(e, habit_list: HabitList):
    new_index = e.args["new_index"]
    logger.info(f"Item drop: {e.args['id']} -> {new_index}")

    # Move element
    elements = ui.context.client.elements
    dragged = elements[int(e.args["id"][1:])]
    assert dragged.parent_slot is not None
    dragged.move(target_index=e.args["new_index"])

    # Unarchive dragged habit
    is_archived = False
    habits = []
    for card in dragged.parent_slot:
        if not isinstance(card, components.HabitOrderCard):
            continue

        if card.habit is None:
            is_archived = True
            continue

        if not is_archived and card.habit.status == HabitStatus.ARCHIVED:
            card.habit.status = HabitStatus.ACTIVE
        if is_archived and card.habit.status == HabitStatus.ACTIVE:
            card.habit.status = HabitStatus.ARCHIVED
        habits.append(card.habit)

    # Update order
    habit_list.order = [str(x.id) for x in habits]
    logger.info(f"New order: {habits}")

    add_ui.refresh()


@ui.refreshable
def add_ui(habit_list: HabitList):
    active_habits = HabitListBuilder(habit_list).status(HabitStatus.ACTIVE).build()
    archived_habits = HabitListBuilder(habit_list).status(HabitStatus.ARCHIVED).build()
    habits = [*active_habits, None, *archived_habits]

    for item in habits:
        with components.HabitOrderCard(item):
            with components.grid(columns=12):
                if item:
                    name = ui.label(item.name)
                    name.classes("col-span-4 col-3")

                    ui.space().classes("col-span-7")

                    btn = HabitDeleteButton(item, habit_list, add_ui.refresh)
                    btn.classes("col-span-1")
                    if item.status == HabitStatus.ACTIVE:
                        btn.classes("invisible")
                else:
                    add = HabitAddButton(habit_list, add_ui.refresh)
                    add.classes("col-span-12")
                    add.props("borderless")


def order_page_ui(habit_list: HabitList):
    with layout():
        with ui.column().classes("pl-1 items-center gap-2"):
            with ui.column().classes("sortable").classes("gap-2"):
                add_ui(habit_list)

    ui.add_body_html(
        """
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
