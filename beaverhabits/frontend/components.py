import calendar
from dataclasses import dataclass
import datetime
from typing import Callable, Optional
from nicegui import events, ui
from nicegui.elements.button import Button

from beaverhabits.storage.dict import DAY_MASK, MONTH_MASK
from beaverhabits.storage.storage import Habit, HabitList
from beaverhabits.frontend import icons
from beaverhabits.configs import settings
from beaverhabits.logging import logger
from beaverhabits.utils import WEEK_DAYS

strptime = datetime.datetime.strptime


def menu_header(title: str, target: str):
    link = ui.link(title, target=target)
    link.classes(
        "text-semibold text-2xl dark:text-white no-underline hover:no-underline"
    )
    return link


def compat_menu(name: str, callback: Callable):
    return ui.menu_item(name, callback).classes("items-center")


def menu_icon_button(icon_name: str, click: Optional[Callable] = None) -> Button:
    button_props = "flat=true unelevated=true padding=xs backgroup=none"
    return ui.button(icon=icon_name, color=None, on_click=click).props(button_props)


class HabitCheckBox(ui.checkbox):
    def __init__(
        self,
        habit: Habit,
        day: datetime.date,
        text: str = "",
        *,
        value: bool = False,
    ) -> None:
        super().__init__(text, value=value, on_change=self._async_task)
        self.habit = habit
        self.day = day
        self._update_style(value)

    def _update_style(self, value: bool):
        self.props(
            f'checked-icon="{icons.DONE}" unchecked-icon="{icons.CLOSE}" keep-color'
        )
        if not value:
            self.props("color=grey-8")
        else:
            self.props("color=currentColor")

    async def _async_task(self, e: events.ValueChangeEventArguments):
        self._update_style(e.value)
        # await asyncio.sleep(5)
        # ui.notify(f"Asynchronous task started: {self.record}")
        await self.habit.tick(self.day, e.value)
        logger.info(f"Day {self.day} ticked: {e.value}")


class HabitNameInput(ui.input):
    def __init__(self, habit: Habit) -> None:
        super().__init__(value=habit.name, on_change=self._async_task)
        self.habit = habit
        self.validation = lambda value: "Too long" if len(value) > 18 else None
        self.props("dense")

    async def _async_task(self, e: events.ValueChangeEventArguments):
        self.habit.name = e.value
        logger.info(f"Habit Name changed to {e.value}")


class HabitStarCheckbox(ui.checkbox):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__("", value=habit.star, on_change=self._async_task)
        self.habit = habit
        self.bind_value(habit, "star")
        self.props(f'checked-icon="{icons.STAR_FULL}" unchecked-icon="{icons.STAR}"')
        self.props("flat fab-mini keep-color color=grey-8")

        self.refresh = refresh

    async def _async_task(self, e: events.ValueChangeEventArguments):
        self.habit.star = e.value
        self.refresh()
        logger.info(f"Habit Star changed to {e.value}")


class HabitDeleteButton(ui.button):
    def __init__(self, habit: Habit, habit_list: HabitList, refresh: Callable) -> None:
        super().__init__(on_click=self._async_task, icon=icons.DELETE)
        self.habit = habit
        self.habit_list = habit_list
        self.refresh = refresh

    async def _async_task(self):
        await self.habit_list.remove(self.habit)
        self.refresh()
        logger.info(f"Deleted habit: {self.habit.name}")


class HabitAddButton(ui.input):
    def __init__(self, habit_list: HabitList, refresh: Callable) -> None:
        super().__init__("New item")
        self.habit_list = habit_list
        self.refresh = refresh
        self.on("keydown.enter", self._async_task)
        self.props("dense")

    async def _async_task(self):
        logger.info(f"Adding new habit: {self.value}")
        await self.habit_list.add(self.value)
        self.refresh()
        self.set_value("")
        logger.info(f"Added new habit: {self.value}")


TODAY = "today"


class HabitDateInput(ui.date):
    def __init__(
        self, today: datetime.date, habit: Habit, ticked_data: dict[datetime.date, bool]
    ) -> None:
        self.today = today
        self.habit = habit
        self.ticked_data = ticked_data
        self.init = True
        self.default_date = today
        super().__init__(self.ticked_days, on_change=self._async_task)

        self.props(f"multiple")
        self.props(f"minimal flat=true")
        self.props(f"default-year-month={self.today.strftime(MONTH_MASK)}")
        self.props(f"first-day-of-week='{settings.FIRST_DAY_OF_WEEK}'")
        # self.props(f"subtitle='{habit.name}'")
        self.classes("shadow-none")

        self.bind_value_from(self, "ticked_days")

    @property
    def ticked_days(self) -> list[str]:
        result = [k.strftime(DAY_MASK) for k, v in self.ticked_data.items() if v]
        # workaround to disable auto focus
        result.append(TODAY)
        return result

    async def _async_task(self, e: events.ValueChangeEventArguments):
        old_values = set(self.habit.ticked_days)
        new_values = set(strptime(x, DAY_MASK).date() for x in e.value if x != TODAY)

        for day in new_values - old_values:
            # self.props(remove="default-date")
            self.props(f"default-year-month={day.strftime(MONTH_MASK)}")
            self.ticked_data[day] = True

            await self.habit.tick(day, True)
            logger.info(f"QDate day {day} ticked: True")

        for day in old_values - new_values:
            # self.props(remove="default-date")
            self.props(f"default-year-month={day.strftime(MONTH_MASK)}")
            self.ticked_data[day] = False

            await self.habit.tick(day, False)
            logger.info(f"QDate day {day} ticked: False")


@dataclass
class HabitCalendar:
    """Habit records by weeks"""

    today: datetime.date
    month_last_day: datetime.date

    headers: list[str]
    data: list[list[datetime.date]]
    week_days: list[str]

    @classmethod
    def build(
        cls, today: datetime.date, weeks: int, firstweekday: int = calendar.MONDAY
    ):
        today = datetime.date.today()
        month_last_day = cls.get_month_last_day(today)

        data = cls.generate_calendar_days(today, weeks, firstweekday)
        headers = cls.generate_calendar_headers(data[0])
        week_day_abbr = [calendar.day_abbr[(firstweekday + i) % 7] for i in range(7)]

        return cls(today, month_last_day, headers, data, week_day_abbr)

    @staticmethod
    def get_month_last_day(today: datetime.date) -> datetime.date:
        month_days = calendar.monthrange(today.year, today.month)[1]
        return datetime.date(today.year, today.month, month_days)

    @staticmethod
    def generate_calendar_headers(days: list[datetime.date]) -> list[str]:
        if not days:
            return []

        result = []
        month = year = None
        for day in days:
            cur_month, cur_year = day.month, day.year
            if cur_month != month:
                result.append(calendar.month_abbr[cur_month])
                month = cur_month
                continue
            if cur_year != year:
                result.append(str(cur_year))
                year = cur_year
                continue
            result.append("")

        return result

    @staticmethod
    def generate_calendar_days(
        today: datetime.date,
        total_days: int,
        firstweekday: int = calendar.MONDAY,  # 0 = Monday, 6 = Sunday
    ) -> list[list[datetime.date]]:
        # First find last day of the month
        last_date_of_month = HabitCalendar.get_month_last_day(today)

        # Then find the last day of the week
        lastweekday = (firstweekday - 1) % 7
        days_delta = (lastweekday - last_date_of_month.weekday()) % 7
        last_date_of_calendar = last_date_of_month + datetime.timedelta(days=days_delta)

        return [
            [
                last_date_of_calendar - datetime.timedelta(days=i, weeks=j)
                for j in reversed(range(total_days))
            ]
            for i in reversed(range(WEEK_DAYS))
        ]


class CalendarCheckBox(ui.checkbox):
    def __init__(
        self,
        habit: Habit,
        day: datetime.date,
        today: datetime.date,
        ticked_data: dict[datetime.date, bool],
    ) -> None:
        self.habit = habit
        self.day = day
        self.today = today
        self.ticked_data = ticked_data
        super().__init__("", value=self.ticked, on_change=self._async_task)

        self.classes("inline-block")
        self.props("dense")
        unchecked_icon, checked_icon = self._icon_svg()
        self.props(f'unchecked-icon="{unchecked_icon}"')
        self.props(f'checked-icon="{checked_icon}"')

        self.bind_value_from(self, "ticked")

    @property
    def ticked(self):
        return self.ticked_data.get(self.day, False)

    def _icon_svg(self):
        unchecked_color, checked_color = "rgb(54,54,54)", "rgb(103,150,207)"
        return (
            icons.SQUARE.format(color=unchecked_color, text=self.day.day),
            icons.SQUARE.format(color=checked_color, text=self.day.day),
        )

    async def _async_task(self, e: events.ValueChangeEventArguments):
        # Update state data
        self.ticked_data[self.day] = e.value

        # Update persistent storage
        await self.habit.tick(self.day, e.value)
        logger.info(f"Calendar Day {self.day} ticked: {e.value}")
