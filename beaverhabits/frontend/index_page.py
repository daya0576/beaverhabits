from nicegui import ui

from beaverhabits.storage.storage import HabitList
from .components import menu_icon_button, habit_check_box, menu_more_button

from beaverhabits.utils import dummy_days


HABIT_LIST_RECORD_COUNT = 5


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

        with grid(2).classes(row_compat_classes):
            for fmt in ("%a", "%d"):
                ui.label("").classes(left_classes)
                for date in dummy_days(HABIT_LIST_RECORD_COUNT):
                    label = ui.label(str(date.strftime(fmt))).classes(right_classes)
                    label.style("color: #9e9e9e; font-size: 85%; font-weight: 500")

        for habit in habits.items:
            with compat_card():
                with grid(1):
                    ui.label(habit.name).classes(left_classes)
                    for record in habit.records:
                        checkbox = habit_check_box(
                            value=record.done, on_change=habit_list_ui.refresh
                        )
                        checkbox.bind_value(record, "done")
                        checkbox.classes(right_classes)


def index_page_ui(habits: HabitList):
    with ui.column().classes("max-w-screen-lg"):
        with ui.row().classes("w-full"):
            ui.label("Habits").classes("text-semibold text-2xl")
            ui.space()
            # menu_icon_button("sym_r_add")
            menu_more_button("sym_r_menu")

        # ui.separator().style("background: hsla(0,0%,100%,.1)")

        habit_list_ui(habits)
