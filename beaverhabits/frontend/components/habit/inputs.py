import datetime
from typing import Callable, Optional
from nicegui import ui, events
from datetime import datetime as strptime

from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.storage.dict import DAY_MASK, MONTH_MASK
from beaverhabits.storage.storage import Habit
from .checkbox import habit_tick

TODAY = "today"
CALENDAR_EVENT_MASK = "%Y/%m/%d"

class WeeklyGoalInput(ui.number):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__(value=habit.weekly_goal or 0, min=0, max=7)
        self.habit = habit
        self.refresh = refresh
        self.props("dense hide-bottom-space")
        self.on("blur", self._async_task)

    async def _async_task(self):
        self.habit.weekly_goal = self.value or 0  # Default to 0 if None
        logger.info(f"Weekly goal changed to {self.habit.weekly_goal}")
        self.refresh()

class HabitNameInput(ui.input):
    def __init__(self, habit: Habit) -> None:
        super().__init__(value=habit.name)
        self.habit = habit
        self.validation = self._validate
        self.props("dense hide-bottom-space")
        self.on("blur", self._async_task)

    async def _async_task(self):
        self.habit.name = self.value
        logger.info(f"Habit Name changed to {self.value}")

    def _validate(self, value: str) -> Optional[str]:
        if not value:
            return "Name is required"
        if len(value) > 130:
            return "Too long"

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
        events = [
            d.strftime(CALENDAR_EVENT_MASK)
            for d, r in self.habit.ticked_data.items()
            if r.text
        ]
        self.props(f'events="{events}" event-color="teal"')

    @property
    def _tick_days(self) -> list[str]:
        ticked_days = [x.strftime(DAY_MASK) for x in self.habit.ticked_days]
        return [*ticked_days, TODAY]

    async def _async_task(self, e: events.ValueChangeEventArguments):
        old_values = set(self.habit.ticked_days)
        new_values = set(strptime(x, DAY_MASK).date() for x in e.value if x != TODAY)

        if diff := new_values - old_values:
            day, value = diff.pop(), True
        elif diff := old_values - new_values:
            day, value = diff.pop(), False
        else:
            return

        self.props(f"default-year-month={day.strftime(MONTH_MASK)}")
        await habit_tick(self.habit, day, bool(value))
        self.value = self._tick_days
