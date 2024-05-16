import os
from nicegui import ui

from beaverhabits.frontend.components import HabitCheckBox, link
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import HabitList
from beaverhabits.utils import dummy_days
from beaverhabits.configs import settings


HABIT_LIST_RECORD_COUNT = settings.INDEX_HABIT_ITEM_COUNT

row_compat_classes = "pl-4 pr-1 py-0"


@ui.refreshable
def habit_list_ui(habits: HabitList):
    if not habits.habits:
        ui.label("List is empty.").classes("mx-auto")
        return

    with ui.column().classes("gap-1.5"):
        # align center vertically
        grid_classes = "w-full gap-0 items-center"
        grid = lambda rows: ui.grid(columns=15, rows=rows).classes(grid_classes)
        left_classes, right_classes = (
            # grid 5
            "col-span-5 break-all",
            # grid 2 2 2 2 2
            "col-span-2 px-1.5 justify-self-center",
        )

        days = dummy_days(HABIT_LIST_RECORD_COUNT)
        with grid(2).classes(row_compat_classes):
            for fmt in ("%a", "%d"):
                ui.label("").classes(left_classes)
                for date in days:
                    label = ui.label(str(date.strftime(fmt))).classes(right_classes)
                    label.style("color: #9e9e9e; font-size: 85%; font-weight: 500")

        for habit in habits.habits:
            with ui.card().classes(row_compat_classes).classes("shadow-none"):
                with grid(1):
                    redirect_page = os.path.join(get_root_path(), "habits", habit.id)
                    habit_name = link(habit.name, target=redirect_page)
                    habit_name.classes(left_classes)

                    d_d = {r.day: r.done for r in habit.records}
                    for day in days:
                        checkbox = HabitCheckBox(habit, day, value=d_d.get(day, False))
                        checkbox.classes(right_classes)


def index_page_ui(habits: HabitList):
    with layout():
        habit_list_ui(habits)
