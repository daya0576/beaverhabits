import datetime
import os

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend import javascript
from beaverhabits.frontend.components import HabitCheckBox, IndexBadge, link
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import HabitList, HabitListBuilder, HabitStatus

HABIT_LIST_RECORD_COUNT = settings.INDEX_DAYS_COUNT


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

    row_compat_classes = "pl-4 pr-1 py-0"
    # Auto hide flex items when it overflows the flex parent
    flex = "flex flex-row-reverse w-full justify-evenly overflow-hidden gap-x-0.5 sm:gap-x-1.5"
    left_classes, right_classes = (
        # grid 4
        f"w-32 sm:w-36 truncate self-center",
        # grid 2 2 2 2 2
        f" self-center",
    )
    header_styles = "font-size: 85%; font-weight: 500; color: #9e9e9e; text-align: center; display: inline-block;"

    # Date Headers
    days = list(reversed(days))
    with ui.column().classes("gap-1.5"):

        with ui.column().classes("gap-0"):
            for it in (week_headers(days), day_headers(days)):
                with ui.row().classes(row_compat_classes).classes("no-wrap gap-0"):
                    ui.label("").classes(left_classes)
                    with ui.element("div").classes(flex).classes("h-4"):
                        for text in it:
                            label = ui.label(text).classes("w-10")
                            label.classes(right_classes)
                            label.style(header_styles)

        # Habit List
        for habit in active_habits:
            with ui.card().classes(row_compat_classes).classes("shadow-none gap-1.5"):
                with ui.row().classes("no-wrap gap-0 h-10"):
                    # truncate name
                    redirect_page = os.path.join(
                        get_root_path(), "habits", str(habit.id)
                    )
                    name = link(habit.name, target=redirect_page)
                    name.classes(left_classes)

                    with ui.element("div").classes(flex).classes("h-10"):
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
