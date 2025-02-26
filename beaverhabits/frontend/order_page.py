from nicegui import ui

from beaverhabits.frontend import components
from beaverhabits.frontend.components import (
    HabitDeleteButton,
    HabitTotalBadge,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.logging import logger
from beaverhabits.sql.models import Habit
from beaverhabits.app.crud import update_habit
from beaverhabits.app.db import User


async def item_drop(e, habits: list[Habit]):
    new_index = e.args["new_index"]
    logger.info(f"Item drop: {e.args['id']} -> {new_index}")

    # Move element
    elements = ui.context.client.elements
    dragged = elements[int(e.args["id"][1:])]
    assert dragged.parent_slot is not None
    dragged.move(target_index=e.args["new_index"])

    # Update habit states
    is_deleted = False
    updated_habits = []
    for card in dragged.parent_slot:
        if not isinstance(card, components.HabitOrderCard):
            continue
        if not card.habit:
            is_deleted = True
            continue

        # Update habit state
        if not is_deleted and card.habit.deleted:
            await update_habit(card.habit.id, card.habit.user_id, deleted=False)
        if is_deleted and not card.habit.deleted:
            await update_habit(card.habit.id, card.habit.user_id, deleted=True)

        # Reset star if moving to deleted section
        if is_deleted and card.habit.star:
            await update_habit(card.habit.id, card.habit.user_id, star=False)

        updated_habits.append(card.habit)

    # Update order
    for i, habit in enumerate(updated_habits):
        await update_habit(habit.id, habit.user_id, order=i)

    logger.info(f"New order: {updated_habits}")
    add_ui.refresh()


@ui.refreshable
async def add_ui(habits: list[Habit]):
    # Split habits into active and deleted
    active_habits = [h for h in habits if not h.deleted]
    deleted_habits = [h for h in habits if h.deleted]
    
    # Sort by order
    active_habits.sort(key=lambda h: h.order)
    deleted_habits.sort(key=lambda h: h.order)
    
    # Combine with separator
    habits = [*active_habits, None, *deleted_habits]

    for item in habits:
        if not item:
            with components.HabitOrderCard(item).classes("p-0"):
                ui.separator().props("w-full size=1.5px")
                continue

        with components.HabitOrderCard(item) as card:
            with ui.row().classes("min-h-10 w-80 items-center"):
                ui.label(item.name)

                ui.space()

                if item.deleted:
                    btn = HabitDeleteButton(item, None, add_ui.refresh)
                    btn.classes("opacity-0")
                    card.btn = btn
                badge = HabitTotalBadge(item)
                badge.props("color=grey-9")

    # Placeholder for moving habit to the end to archive
    ui.space()


async def order_page_ui(habits: list[Habit], user: User | None = None, current_list_id: str | int | None = None):
    async with layout(user=user, current_list_id=current_list_id):
        with ui.column().classes("items-center sortable gap-2 w-full"):
            await add_ui(habits)

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

    ui.on("item_drop", lambda e: item_drop(e, habits))
