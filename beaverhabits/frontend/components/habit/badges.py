from nicegui import ui

from beaverhabits.storage.storage import Habit

class HabitTotalBadge(ui.badge):
    def __init__(self, habit: Habit) -> None:
        super().__init__()
        self.bind_text_from(habit, "ticked_days", backward=lambda x: str(len(x)))

class IndexBadge(HabitTotalBadge):
    def __init__(self, habit: Habit) -> None:
        super().__init__(habit)
        self.props("color=grey-9 rounded transparent")
        self.style("font-size: 80%; font-weight: 500")
