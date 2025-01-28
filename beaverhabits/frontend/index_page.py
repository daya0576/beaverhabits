import datetime
import os

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend import javascript
from beaverhabits.frontend.components import HabitCheckBox, IndexBadge, link
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import HabitList, HabitListBuilder, HabitStatus

HABIT_LIST_RECORD_COUNT = settings.INDEX_HABIT_ITEM_COUNT


def grid(columns, rows):
    g = ui.grid(columns=columns, rows=rows)
    g.classes("w-full gap-0 items-center")
    return g


def week_headers(days: list[datetime.date]):
    for day in days:
        yield day.strftime("%a")
    if settings.INDEX_SHOW_HABIT_COUNT:
        yield "Sum"


def day_headers(days: list[datetime.date]):
    for day in days:
        yield day.strftime("%d")
    if settings.INDEX_SHOW_HABIT_COUNT:
        yield "#"


@ui.refreshable
def habit_list_ui(days: list[datetime.date], habit_list: HabitList):
    active_habits = HabitListBuilder(habit_list).status(HabitStatus.ACTIVE).build()
    if not active_habits:
        ui.label("List is empty.").classes("mx-auto w-80")
        return

    # Calculate column count
    name_columns, date_columns = 4, 2
    count_columns = 2 if settings.INDEX_SHOW_HABIT_COUNT else 0
    columns = name_columns + len(days) * date_columns + count_columns

    row_compat_classes = "pl-4 pr-1 py-0"
    left_classes, right_classes = (
        # grid 4
        f"col-span-{name_columns} truncate",
        # grid 2 2 2 2 2
        f"col-span-{date_columns} px-1.5 justify-self-center",
    )
    header_styles = "font-size: 85%; font-weight: 500; color: #9e9e9e"

    with ui.column().classes("gap-1.5"):
        # Date Headers
        with grid(columns, 2).classes(row_compat_classes):
            for it in (week_headers(days), day_headers(days)):
                ui.label("").classes(left_classes)
                for label in it:
                    ui.label(label).classes(right_classes).style(header_styles)

        # Habit List
        for habit in active_habits:
            with ui.card().classes(row_compat_classes).classes("shadow-none"):
                with grid(columns, 1):
                    # truncate name
                    root_path = get_root_path()
                    redirect_page = os.path.join(root_path, "habits", str(habit.id))
                    name = link(habit.name, target=redirect_page).classes(left_classes)
                    name.style(f"max-width: {52 * name_columns / date_columns}px;")

                    ticked_days = set(habit.ticked_days)
                    for day in days:
                        checkbox = HabitCheckBox(habit, day, day in ticked_days)
                        checkbox.classes(right_classes)

                    if settings.INDEX_SHOW_HABIT_COUNT:
                        IndexBadge(habit).classes(right_classes)


def index_page_ui(days: list[datetime.date], habits: HabitList):
    with layout():
        habit_list_ui(days, habits)

    # Prevent long press context menu for svg image elements
    ui.context.client.on_connect(javascript.prevent_context_menu)
