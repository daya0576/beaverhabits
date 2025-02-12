from nicegui import ui

from beaverhabits.storage.storage import Habit, HabitStatus

class HabitOrderCard(ui.card):
    def __init__(self, habit: Habit | None = None) -> None:
        super().__init__()
        self.habit = habit
        self.props("flat dense")
        self.classes("py-0 w-full")

        # Drag and drop
        self.props("draggable")
        self.classes("cursor-grab")
        if not habit or habit.status == HabitStatus.ARCHIVED:
            self.classes("opacity-50")

        # Button to delete habit
        self.btn: ui.button | None = None
        self.on(
            "mouseover", lambda: self.btn and self.btn.classes("transition opacity-100")
        )
        self.on("mouseout", lambda: self.btn and self.btn.classes(remove="opacity-100"))
