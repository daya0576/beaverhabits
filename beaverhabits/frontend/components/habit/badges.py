from nicegui import ui

from beaverhabits.sql.models import Habit
from beaverhabits.app.crud import get_habit_checks

class HabitTotalBadge(ui.badge):
    def __init__(self, habit: Habit) -> None:
        super().__init__()
        # Count completed records
        completed_count = sum(1 for record in habit.checked_records if record.done)
        self.text = str(completed_count)

class IndexBadge(HabitTotalBadge):
    def __init__(self, habit: Habit) -> None:
        super().__init__(habit)
        self.props("color=grey-9 rounded transparent")
        self.style("font-size: 80%; font-weight: 500")
