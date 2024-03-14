import random

from nicegui import ui

from .components import build_check_box
from .utils import dummy_days, dummy_records
from .models import Habit, HabitList


HABIT_LIST_RECORD_COUNT = 5


@ui.refreshable
def habit_list_ui():
    if not habits.items:
        ui.label("List is empty.").classes("mx-auto")
        return

    with ui.column().classes("gap-2"):
        # compat card
        row_compat_classes = "pl-4 pr-1 py-0.5"
        compat_card = (
            lambda: ui.card().classes(row_compat_classes).classes("shadow-none")
        )

        # grid: 5 | 2 2 2 2 2
        grid_classes = "w-full gap-0 items-center"
        grid = lambda rows: ui.grid(columns=15, rows=rows).classes(grid_classes)
        left_classes, right_classes = (
            "col-span-5 break-all",
            "col-span-2 justify-self-center px-1.5",
        )

        # header
        with grid(2).classes(row_compat_classes):
            for fmt in ("%a", "%d"):
                ui.label("").classes(left_classes)
                for date in dummy_days(HABIT_LIST_RECORD_COUNT):
                    label = ui.label(str(date.strftime(fmt))).classes(right_classes)
                    label.style("color: #9e9e9e; font-size: 85%; font-weight: 500")

        # body
        for habit in habits.items:
            with compat_card():
                with grid(1):
                    ui.label(habit.name).classes(left_classes)
                    for record in habit.items:
                        checkbox = build_check_box(
                            value=record.done, on_change=habit_list_ui.refresh
                        )
                        checkbox.bind_value(record, "done")
                        checkbox.classes(right_classes)


def main_page():
    with ui.column().classes("max-w-screen-lg"):
        ui.label().bind_text_from(habits, "title").classes("text-semibold text-2xl")
        # ui.separator().props("color=grey-8 ")
        habit_list_ui()
        # add_input = ui.input("New item").classes("mx-12")
        # add_input.on(
        #     "keydown.enter", lambda: (habits.add(add_input.value), add_input.set_value(""))
        # )


habits = HabitList("Habits", on_change=habit_list_ui.refresh)
for name in ["Order pizz", "Running", "Table Tennis", "Clean", "Call mom"]:
    pick = lambda: random.randint(0, 3) == 0
    habit = Habit(name, items=dummy_records(HABIT_LIST_RECORD_COUNT, pick=pick))
    habits.add(habit)

main_page()
ui.run(dark=True)
