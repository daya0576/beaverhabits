import calendar
import datetime
from dataclasses import dataclass
from typing import Callable, Optional

from dateutil.relativedelta import relativedelta
from nicegui import events, ui
from nicegui.elements.button import Button

from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.storage.dict import DAY_MASK, MONTH_MASK
from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList, HabitStatus
from beaverhabits.utils import WEEK_DAYS

strptime = datetime.datetime.strptime


def link(text: str, target: str):
    return ui.link(text, target=target).classes(
        "dark:text-white  no-underline hover:no-underline"
    )


def menu_header(title: str, target: str):
    link = ui.link(title, target=target)
    link.classes(
        "text-semibold text-2xl dark:text-white no-underline hover:no-underline"
    )
    return link


def compat_menu(name: str, callback: Callable):
    return ui.menu_item(name, callback).props("dense").classes("items-center")


def menu_icon_button(
    icon_name: str, click: Optional[Callable] = None, tooltip: str | None = None
) -> Button:
    button_props = "flat=true unelevated=true padding=xs backgroup=none"
    button = ui.button(icon=icon_name, color=None, on_click=click).props(button_props)
    if tooltip:
        button = button.tooltip(tooltip)
    return button


def habit_tick_dialog(record: CheckedRecord | None):
    text = record.text if record else ""
    with ui.dialog() as dialog, ui.card():
        t = ui.textarea(label="Note", value=text)
        with ui.row():
            ui.button("Yes", on_click=lambda: dialog.submit((True, t.value)))
            ui.button("No", on_click=lambda: dialog.submit((False, None)))
    return dialog


async def habit_tick(
    habit: Habit, day: datetime.date, value: bool
) -> CheckedRecord | None:
    # Transaction start
    await habit.tick(day, value)
    logger.info(f"Day {day} ticked: {value}")

    # Daily notes/short description
    if habit.note and value:
        record = habit.record_by(day)
        yes, text = await habit_tick_dialog(record)

        # Rollback if user cancel
        if not yes:
            await habit.tick(day, not value, text)
            logger.info(f"Day {day} ticked: {not value} (rollback)")


class HabitCheckBox(ui.checkbox):
    def __init__(self, habit: Habit, day: datetime.date) -> None:
        self.habit = habit
        self.day = day

        super().__init__("", value=self._value, on_change=self._async_task)
        self._update_style(self._value)

        self.bind_value_from(self, "_value")

    def _update_style(self, value: bool):
        self.props(
            f'checked-icon="{icons.DONE}" unchecked-icon="{icons.CLOSE}" keep-color'
        )
        if not value:
            self.props("color=grey-8")
        else:
            self.props("color=currentColor")

    @property
    def _value(self) -> bool:
        record = self.habit.record_by(self.day)
        result = bool(record and record.done)
        return result

    async def _async_task(self, e: events.ValueChangeEventArguments):
        self._update_style(e.value)

        # Do update completion status
        await habit_tick(self.habit, self.day, e.value)


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
        if len(value) > 18:
            return "Too long"


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


class HabitEditButton(ui.button):
    def __init__(self, habit: Habit) -> None:
        super().__init__(on_click=self._async_task, icon="edit_square")
        self.habit = habit
        self.props("flat fab-mini color=grey-8")

    async def _async_task(self):
        pass


class HabitDeleteButton(ui.button):
    def __init__(self, habit: Habit, habit_list: HabitList, refresh: Callable) -> None:
        icon = icons.DELETE if habit.status == HabitStatus.ACTIVE else icons.DELETE_F
        super().__init__(on_click=self._async_task, icon=icon)
        self.habit = habit
        self.habit_list = habit_list
        self.refresh = refresh
        self.props("flat fab-mini color=grey-9")

        # Double confirm dialog to delete habit
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Are you sure to delete habit: {habit.name}?")
            with ui.row():
                ui.button("Yes", on_click=lambda: dialog.submit(True))
                ui.button("No", on_click=lambda: dialog.submit(False))
        self.dialog = dialog

    async def _async_task(self):
        if self.habit.status == HabitStatus.ACTIVE:
            self.habit.status = HabitStatus.ARCHIVED
            logger.info(f"Archive habit: {self.habit.name}")

        elif self.habit.status == HabitStatus.ARCHIVED:
            if not await self.dialog:
                return
            self.habit.status = HabitStatus.SOLF_DELETED
            logger.info(f"Soft delete habit: {self.habit.name}")

        self.refresh()


class HabitAddButton(ui.input):
    def __init__(self, habit_list: HabitList, refresh: Callable) -> None:
        super().__init__("New item")
        self.habit_list = habit_list
        self.refresh = refresh
        self.on("keydown.enter", self._async_task)
        self.props('dense color="white" label-color="white"')

    async def _async_task(self):
        await self.habit_list.add(self.value)
        logger.info(f"Added new habit: {self.value}")
        self.refresh()
        self.set_value("")


TODAY = "today"


class HabitDateInput(ui.date):
    def __init__(
        self,
        today: datetime.date,
        habit: Habit,
    ) -> None:
        self.today = today
        self.habit = habit
        # self.init = True
        # self.default_date = today
        super().__init__(self._tick_days, on_change=self._async_task)

        self.props("multiple minimal flat today-btn")
        self.props(f"default-year-month={self.today.strftime(MONTH_MASK)}")
        self.props(f"first-day-of-week='{(settings.FIRST_DAY_OF_WEEK + 1) % 7}'")

        self.classes("shadow-none")

        self.bind_value_from(self, "_tick_days")

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


@dataclass
class CalendarHeatmap:
    """Habit records by weeks"""

    today: datetime.date

    headers: list[str]
    data: list[list[datetime.date]]
    week_days: list[str]

    @classmethod
    def build(
        cls, today: datetime.date, weeks: int, firstweekday: int = calendar.MONDAY
    ):
        data = cls.generate_calendar_days(today, weeks, firstweekday)
        headers = cls.generate_calendar_headers(data[0])
        week_day_abbr = [calendar.day_abbr[(firstweekday + i) % 7] for i in range(7)]

        return cls(today, headers, data, week_day_abbr)

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
        total_weeks: int,
        firstweekday: int = calendar.MONDAY,  # 0 = Monday, 6 = Sunday
    ) -> list[list[datetime.date]]:
        # Find the last day of the week
        lastweekday = (firstweekday - 1) % 7
        days_delta = (lastweekday - today.weekday()) % 7
        last_date_of_calendar = today + datetime.timedelta(days=days_delta)

        return [
            [
                last_date_of_calendar - datetime.timedelta(days=i, weeks=j)
                for j in reversed(range(total_weeks))
            ]
            for i in reversed(range(WEEK_DAYS))
        ]


class CalendarCheckBox(ui.checkbox):
    def __init__(
        self,
        habit: Habit,
        day: datetime.date,
        today: datetime.date,
        is_bind_data: bool = True,
    ) -> None:
        self.habit = habit
        self.day = day
        self.today = today
        super().__init__("", value=self.ticked, on_change=self._async_task)

        self.classes("inline-block")
        self.props("dense")
        unchecked_icon, checked_icon = self._icon_svg()
        self.props(f'unchecked-icon="{unchecked_icon}"')
        self.props(f'checked-icon="{checked_icon}"')

        if is_bind_data:
            self.bind_value_from(self, "ticked")

    @property
    def ticked(self) -> bool:
        record = self.habit.ticked_data.get(self.day)
        return bool(record and record.done)

    def _icon_svg(self):
        unchecked_color, checked_color = "rgb(54,54,54)", "rgb(103,150,207)"
        return (
            icons.SQUARE.format(color=unchecked_color, text=self.day.day),
            icons.SQUARE.format(color=checked_color, text=self.day.day),
        )

    async def _async_task(self, e: events.ValueChangeEventArguments):
        # Update persistent storage
        await self.habit.tick(self.day, e.value)
        logger.info(f"Day {self.day} ticked: {e.value}")


def habit_heat_map(
    habit: Habit,
    habit_calendar: CalendarHeatmap,
    readonly: bool = False,
):
    today = habit_calendar.today

    # Bind to external state data
    is_bind_data = not readonly

    # Headers
    with ui.row(wrap=False).classes("gap-0"):
        for header in habit_calendar.headers:
            header_lable = ui.label(header).classes("text-gray-300 text-center")
            header_lable.style("width: 20px; line-height: 18px; font-size: 9px;")
        ui.label().style("width: 22px;")

    # Day matrix
    for i, weekday_days in enumerate(habit_calendar.data):
        with ui.row(wrap=False).classes("gap-0"):
            for day in weekday_days:
                if day <= habit_calendar.today:
                    CalendarCheckBox(habit, day, today, is_bind_data)
                else:
                    ui.label().style("width: 20px; height: 20px;")

            week_day_abbr_label = ui.label(habit_calendar.week_days[i])
            week_day_abbr_label.classes("indent-1.5 text-gray-300")
            week_day_abbr_label.style("width: 22px; line-height: 20px; font-size: 9px;")


def grid(columns: int, rows: int | None = 1) -> ui.grid:
    return ui.grid(columns=columns, rows=rows).classes("gap-0 items-center")


def habit_history(today: datetime.date, ticked_days: list[datetime.date]):
    # get lastest 6 months, e.g. Feb
    months, data = [], []
    for i in range(13, 0, -1):
        offset_date = today - relativedelta(months=i)
        months.append(offset_date.strftime("%b"))

        count = sum(
            1
            for x in ticked_days
            if x.month == offset_date.month and x.year == offset_date.year
        )
        data.append(count)

    echart = ui.echart(
        {
            "xAxis": {
                "data": months,
            },
            "yAxis": {
                "type": "value",
                "position": "right",
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#303030",
                    },
                },
            },
            "series": [
                {
                    "type": "line",
                    "data": data,
                    "itemStyle": {"color": icons.current_color},
                    "animation": False,
                }
            ],
            "grid": {
                "top": 15,
                "bottom": 25,
                "left": 5,
                "right": 30,
                "show": False,
            },
        }
    )
    echart.classes("h-40")


class HabitTotalBadge(ui.badge):
    def __init__(self, habit: Habit) -> None:
        super().__init__()
        self.bind_text_from(habit, "ticked_days", backward=lambda x: str(len(x)))


class IndexBadge(HabitTotalBadge):
    def __init__(self, habit: Habit) -> None:
        super().__init__(habit)
        self.props("color=grey-9 rounded transparent")
        self.style("font-size: 80%; font-weight: 500")


class HabitNotesExpansion(ui.expansion):
    def __init__(self, title, habit: Habit) -> None:
        is_expanded = bool(habit.note)

        super().__init__(
            title,
            icon=" ",
            value=is_expanded,
            on_value_change=self._async_task,
        )
        self.habit = habit
        self.props("dense")
        self.classes("w-full text-base text-center")

        self.bind_value_from(self, "value")

    async def _async_task(self, e: events.ValueChangeEventArguments):
        if e.value == self.habit.note:
            return
        if not await self.confirm_dialog():
            self.value = self.habit.note
            return

        self.habit.note = e.value
        logger.info(f"Habit Note changed to {e.value}")

    def confirm_dialog(self):
        msg = "enable" if not self.habit.note else "disable"
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Are you sure to {msg} notes?")
            with ui.row():
                ui.button("Yes", on_click=lambda: dialog.submit(True))
                ui.button("No", on_click=lambda: dialog.submit(False))
        return dialog
