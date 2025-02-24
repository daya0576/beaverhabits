import datetime
from typing import Callable, Optional
from nicegui import ui, events

from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.sql.models import Habit
from beaverhabits.app.crud import update_habit, get_habit_checks
from .checkbox import habit_tick

TODAY = "today"
DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"
CALENDAR_EVENT_MASK = "%Y/%m/%d"

class WeeklyGoalInput(ui.number):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__(value=habit.weekly_goal or 0, min=0, max=7)
        self.habit = habit
        self.props("dense hide-bottom-space")

    def _validate(self, value: str) -> Optional[str]:
        if value is None or value < 0 or value > 7:
            return "Value must be between 0 and 7"

    def get_value(self) -> int:
        return self.value

class HabitNameInput(ui.input):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__(value=habit.name)
        self.habit = habit
        self.validation = self._validate
        self.props("dense hide-bottom-space")

    def _validate(self, value: str) -> Optional[str]:
        if not value:
            return "Name is required"
        if len(value) > 130:
            return "Too long"

    def get_value(self) -> str:
        return self.value

class HabitDateInput(ui.date):
    def __init__(
        self,
        today: datetime.date,
        habit: Habit,
    ) -> None:
        self.today = today
        self.habit = habit
        super().__init__(self._tick_days, on_change=self._async_task)

        self.props("multiple minimal flat today-btn")
        self.props(f"default-year-month={self.today.strftime(MONTH_MASK)}")
        self.props(f"first-day-of-week='{(settings.FIRST_DAY_OF_WEEK + 1) % 7}'")

        self.classes("shadow-none")

        self.bind_value_from(self, "_tick_days")
        # Get events (days with notes)
        events = [
            r.day.strftime(CALENDAR_EVENT_MASK)
            for r in habit.checked_records
            if hasattr(r, 'text') and r.text
        ]
        self.props(f'events="{events}" event-color="teal"')

    @property
    async def _tick_days(self) -> list[str]:
        # Get completed days
        records = await get_habit_checks(self.habit.id, self.habit.user_id)
        ticked_days = [r.day.strftime(DAY_MASK) for r in records if r.done]
        return [*ticked_days, TODAY]

    async def _async_task(self, e: events.ValueChangeEventArguments):
        # Get current completed days
        records = await get_habit_checks(self.habit.id, self.habit.user_id)
        old_values = {r.day for r in records if r.done}
        value = await e.value
        new_values = set()
        for x in value:
            if x and x != TODAY:
                try:
                    date = datetime.datetime.strptime(x, DAY_MASK).date()
                    new_values.add(date)
                except ValueError:
                    logger.warning(f"Invalid date format: {x}")

        if diff := new_values - old_values:
            day, value = diff.pop(), True
        elif diff := old_values - new_values:
            day, value = diff.pop(), False
        else:
            return


        self.props(f"default-year-month={day.strftime(MONTH_MASK)}")
        await habit_tick(self.habit, day, bool(value))
        self.value = await self._tick_days
