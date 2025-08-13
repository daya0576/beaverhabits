from nicegui import ui

from beaverhabits.frontend import components
from beaverhabits.frontend.components import (
    HabitDeleteButton,
    HabitTotalBadge,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.logger import logger
from beaverhabits.storage.storage import (
    HabitList,
    HabitListBuilder,
    HabitOrder,
    HabitStatus,
)


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
        if not card.habit:
            is_archived = True
            continue

        if not is_archived and card.habit.status == HabitStatus.ARCHIVED:
            card.habit.status = HabitStatus.ACTIVE
        if is_archived and card.habit.status == HabitStatus.ACTIVE:
            card.habit.status = HabitStatus.ARCHIVED

        if card.habit.star:
            card.habit.star = False

        habits.append(card.habit)

    # Update order
    habit_list.order = [str(x.id) for x in habits]
    habit_list.order_by = HabitOrder.MANUALLY
    logger.info(f"New order: {habits}")

    add_ui.refresh()


@ui.refreshable
def add_ui(habit_list: HabitList):
    active_habits = HabitListBuilder(habit_list).status(HabitStatus.ACTIVE).build()
    archived_habits = HabitListBuilder(habit_list).status(HabitStatus.ARCHIVED).build()
    habits = [*active_habits, None, *archived_habits]

    for item in habits:
        if not item:
            with components.HabitOrderCard(item).classes("p-0"):
                ui.separator().props("w-full size=1.5px")
                continue

        with components.HabitOrderCard(item) as card:
            with ui.row().classes("min-h-10 w-80 items-center gap-2"):
                ui.label(item.name)

                ui.space()

                if item.status == HabitStatus.ARCHIVED:
                    btn = HabitDeleteButton(item, habit_list, add_ui.refresh)
                    btn.classes("opacity-0")
                    card.btn = btn

                for tag in item.tags:
                    ui.badge(tag).props("color=grey-9")

                badge = HabitTotalBadge(item)
                badge.props("color=grey-9")

    # Placeholder for moving habit to the end to archive
    ui.space()


def order_page_ui(habit_list: HabitList):
    with layout(habit_list=habit_list):
        with ui.column().classes("items-center sortable gap-2 w-full"):
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
