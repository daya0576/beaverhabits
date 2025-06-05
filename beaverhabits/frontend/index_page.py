import datetime
import os
from collections import OrderedDict
from typing import List

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.core.completions import get_habit_date_completion
from beaverhabits.frontend import javascript
from beaverhabits.frontend.components import (
    HabitCheckBox,
    IndexBadge,
    TagManager,
    habits_by_tags,
    link,
    tag_filter_component,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import (
    Habit,
    HabitList,
    HabitListBuilder,
    HabitStatus,
)

NAME_COLS, DATE_COLS = settings.INDEX_HABIT_NAME_COLUMNS, 2
COUNT_BADGE_COLS = 2 if settings.INDEX_SHOW_HABIT_COUNT else 0
LEFT_CLASSES, RIGHT_CLASSES = (
    # grid 5
    f"col-span-{NAME_COLS} truncate max-w-[{24 * NAME_COLS}px]",
    # grid 2 2 2 2 2
    f"col-span-{DATE_COLS} px-1 place-self-center",
)
COMPAT_CLASSES = "pl-4 pr-0 py-0 dark:shadow-none"

# Sticky date row for long habit list
STICKY_STYLES = "position: sticky; top: 0; z-index: 1;"


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


def habit_row(habit: Habit, tag: str, days: list[datetime.date]):
    # truncate name
    root_path = get_root_path()
    redirect_page = os.path.join(root_path, "habits", str(habit.id))
    name = link(habit.name, target=redirect_page)
    name.classes(LEFT_CLASSES)
    name.props(f'role="heading" aria-level="2" aria-label="{habit.name}"')

    today = max(days)
    status_map = get_habit_date_completion(habit, min(days), today)
    for day in days:
        status = status_map.get(day, [])
        checkbox = HabitCheckBox(
            status, habit, today, day, refresh=habit_list_ui.refresh
        )
        checkbox.classes(RIGHT_CLASSES)
        # checkbox.classes("theme-icon-lazy invisible")

    if settings.INDEX_SHOW_HABIT_COUNT:
        IndexBadge(today, habit).classes(RIGHT_CLASSES)


@ui.refreshable
def habit_list_ui(days: list[datetime.date], active_habits: List[Habit]):
    # Total cloumn for each row
    columns = NAME_COLS + len(days) * DATE_COLS + COUNT_BADGE_COLS

    with ui.column().classes("gap-1.5"):
        # Date Headers
        with grid(columns, 2).classes(COMPAT_CLASSES).style(STICKY_STYLES) as g:
            g.props('aria-hidden="true"').classes("theme-header-date")
            for it in (week_headers(days), day_headers(days)):
                ui.label("").classes(LEFT_CLASSES)
                for label in it:
                    ui.label(label).classes(RIGHT_CLASSES)

        # Habit Rows
        groups = habits_by_tags(active_habits)
        if len(groups) > 1:
            if selected_tags := TagManager.get_all():
                groups = OrderedDict(
                    (k, v) for k, v in groups.items() if k in selected_tags
                )

        for tag, habit_list in groups.items():
            if not habit_list:
                continue

            for habit in habit_list:
                with ui.card().classes(COMPAT_CLASSES).classes("theme-card-shadow"):
                    with grid(columns, 1):
                        habit_row(habit, tag, days)

            ui.space()


def index_page_ui(days: list[datetime.date], habits: HabitList):
    active_habits = HabitListBuilder(habits).status(HabitStatus.ACTIVE).build()
    if not active_habits:
        ui.label("List is empty.").classes("mx-auto w-80")
        return

    if settings.INDEX_HABIT_DATE_REVERSE:
        days = list(reversed(days))

    with layout(habit_list=habits):
        # Category
        tag_filter_component(active_habits, refresh=habit_list_ui.refresh)
        habit_list_ui(days, active_habits)

    # placeholder to preload js cache (daily notes)
    ui.input("").classes("hidden").props('aria-hidden="true"')
    # Prevent long press context menu for svg image elements
    ui.context.client.on_connect(javascript.prevent_context_menu)
