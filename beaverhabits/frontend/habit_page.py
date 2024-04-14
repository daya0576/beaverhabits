from nicegui import ui
from beaverhabits.frontend.components import HabitDateInput
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import Habit


def habit_page_ui(habit: Habit):
    with layout():
        with ui.column().classes("gap-1.5"):
            HabitDateInput(habit)
