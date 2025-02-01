import datetime
import os
from contextlib import contextmanager
from typing import Iterable

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend import javascript
from beaverhabits.frontend.components import HabitCheckBox, IndexBadge, link
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import Habit, HabitList, HabitListBuilder, HabitStatus

HABIT_LIST_RECORD_COUNT = settings.INDEX_DAYS_COUNT

LEFT_ITEM_CLASSES = "min-w-[110px] truncate self-center"
RIGHT_ITEM_CLASSES = "w-10 self-center"


def week_headers(days: list[datetime.date]):
    if settings.INDEX_SHOW_HABIT_COUNT:
        yield "Sum"
    for day in days:
        yield day.strftime("%a")


def day_headers(days: list[datetime.date]):
    if settings.INDEX_SHOW_HABIT_COUNT:
        yield "#"
    for day in days:
        yield day.strftime("%d")


@contextmanager
def row():
    with ui.row().classes("pl-4 pr-1 py-0").classes("no-wrap gap-0"):
        yield


@contextmanager
def card():
    with ui.card().classes("shadow-none gap-1.5 p-0"):
        with row():
            yield


@contextmanager
def flex(height: int):
    # Responsive flex container
    with ui.element("div") as f:
        # Auto hide flex items when it overflows the flex parent
        f.classes("flex flex-row-reverse justify-evenly")
        # Auto ajust gap with screen size
        f.classes(
            "gap-x-0"
            "md:gap-x-[6px] "
            "lg:gap-x-[8px] "
            # "xl:gap-x-[8px] "
            # ...
        )
        f.classes(
            f"max-w-[{40*6-1}px] "
            f"md:max-w-[{40*7 + (7-1)*6}px] "
            f"lg:max-w-[{40*10 + (10-1)*8}px] "
            # f"xl:max-w-[{40*14 + 10*(14-1)*8}px] "
            # ...
        )
        # Auto hide overflowed items
        f.classes(f"overflow-hidden h-{height}")
        yield f


def name(habit: Habit):
    # truncate name
    redirect_page = os.path.join(get_root_path(), "habits", str(habit.id))
    name = link(habit.name, target=redirect_page)
    name.classes(LEFT_ITEM_CLASSES)


def headers(labels: Iterable[str]):
    with flex(4):
        for text in labels:
            label = ui.label(text)
            label.classes(RIGHT_ITEM_CLASSES)
            label.style(
                "font-size: 85%; font-weight: 500; color: #9e9e9e; text-align: center"
            )


def checkboxes(habit: Habit, days: list[datetime.date]):
    with flex(10):
        if settings.INDEX_SHOW_HABIT_COUNT:
            with ui.element("div").classes("w-10 h-10 flex place-content-center"):
                IndexBadge(habit)

        ticked_days = set(habit.ticked_days)
        for day in days:
            checkbox = HabitCheckBox(habit, day, day in ticked_days)
            checkbox.classes(RIGHT_ITEM_CLASSES)


@ui.refreshable
def habit_list_ui(days: list[datetime.date], habit_list: HabitList):
    active_habits = HabitListBuilder(habit_list).status(HabitStatus.ACTIVE).build()
    if not active_habits:
        ui.label("List is empty.")
        return

    days = list(reversed(days))

    with ui.column().classes("gap-1.5"):
        # Date Headers
        with ui.column().classes("gap-0"):
            for it in (week_headers(days), day_headers(days)):
                with row():
                    ui.label("").classes(LEFT_ITEM_CLASSES)
                    headers(it)

        # Habit List
        for habit in active_habits:
            with card():
                # Truncated habit name
                name(habit)
                checkboxes(habit, days)


def index_page_ui(days: list[datetime.date], habits: HabitList):
    with layout():
        habit_list_ui(days, habits)

    # Prevent long press context menu for svg image elements
    ui.context.client.on_connect(javascript.prevent_context_menu)
