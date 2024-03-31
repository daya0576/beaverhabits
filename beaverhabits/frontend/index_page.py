import asyncio
from nicegui import events, ui
from beaverhabits.frontend.layout import layout

from beaverhabits.storage.storage import HabitList
from .components import HabitCheckBox, habit_check_box

from beaverhabits.utils import dummy_days


HABIT_LIST_RECORD_COUNT = 5


async def async_task(e: events.ValueChangeEventArguments):
    ui.notify(f"Asynchronous task started: {e.value}")
    ui.notify(f"Asynchronous task started: {e.sender.record}")
    ui.notify(f"Asynchronous task started: {e.sender.habit}")
    # ui.notify(f"Asynchronous task started: {habit}, {record}")
    # if record not in habit.records:
    #     habit.records.append(record)
    await asyncio.sleep(1)
    ui.notify("Asynchronous task finished")


@ui.refreshable
def habit_list_ui(habits: HabitList):
    if not habits.items:
        ui.label("List is empty.").classes("mx-auto")
        return

    with ui.column().classes("gap-1.5"):
        # custom padding
        row_compat_classes = "pl-4 pr-1 py-0"
        compat_card = (
            lambda: ui.card().classes(row_compat_classes).classes("shadow-none")
        )
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

        for habit in habits.items:
            with compat_card():
                with grid(1):
                    ui.label(habit.name).classes(left_classes)
                    for record in habit.get_records_by_date(days).values():
                        checkbox = HabitCheckBox(habit, record, value=record.done)
                        checkbox.classes(right_classes)


def index_page_ui(habits: HabitList, root_path: str):
    with layout(root_path):
        habit_list_ui(habits)
