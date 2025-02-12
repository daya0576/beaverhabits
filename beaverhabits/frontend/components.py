import asyncio
import calendar
import datetime
from dataclasses import dataclass
from typing import Callable, List, Optional

from dateutil.relativedelta import relativedelta
from nicegui import events, ui
from nicegui.elements.button import Button

from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.storage.dict import DAY_MASK, MONTH_MASK
from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList, HabitStatus
from beaverhabits.utils import WEEK_DAYS, ratelimiter

strptime = datetime.datetime.strptime

DAILY_NOTE_MAX_LENGTH = 300
CALENDAR_EVENT_MASK = "%Y/%m/%d"


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
    with ui.dialog() as dialog, ui.card().props("flat") as card:
        dialog.props('backdrop-filter="blur(4px)"')
        card.classes("w-5/6 max-w-80")

        with ui.column().classes("gap-0 w-full"):
            t = ui.textarea(
                label="Note",
                value=text,
                validation={
                    "Too long!": lambda value: len(value) < DAILY_NOTE_MAX_LENGTH
                },
            )
            t.classes("w-full")

            with ui.row():
                ui.button("Yes", on_click=lambda: dialog.submit((True, t.value))).props(
                    "flat"
                )
                ui.button("No", on_click=lambda: dialog.submit((False, t.value))).props(
                    "flat"
                )
    return dialog


async def note_tick(habit: Habit, day: datetime.date) -> bool | None:
    record = habit.record_by(day)
    result = await habit_tick_dialog(record)

    if result is None:
        return

    yes, text = result
    if text and len(text) > DAILY_NOTE_MAX_LENGTH:
        ui.notify("Note is too long", color="negative")
        return

    record = await habit.tick(day, yes, text)
    logger.info(f"Habit ticked: {day} {yes}, note: {text}")
    return record.done


@ratelimiter(limit=30, window=30)
@ratelimiter(limit=10, window=1)
async def habit_tick(habit: Habit, day: datetime.date, value: bool | None):
    # Avoid duplicate tick
    record = habit.record_by(day)
    if record and record.done is value:  # Use 'is' to handle None case correctly
        return

    # Transaction start
    await habit.tick(day, value)
    logger.info(f"Day {day} ticked: {value}")


class HabitCheckBox(ui.checkbox):
    def __init__(self, habit: Habit, day: datetime.date, value: bool | None, refresh: Callable | None = None) -> None:
        super().__init__("", value=bool(value))  # Convert None to False for initial state
        self.habit = habit
        self.day = day
        self.refresh = refresh
        self.skipped = value is None  # Track skipped state
        text_color = "chartreuse" if self.day == datetime.date.today() else "white"
        self.unchecked_icon = icons.SQUARE.format(color="rgb(54,54,54)", text=self.day.day, text_color=text_color)
        self.checked_icon = icons.DONE
        self.skipped_icon = icons.CLOSE
        self._update_icons()
        self._update_style(value)

        # Hold on event flag
        self.hold = asyncio.Event()
        self.moving = False

        # Sequence of events: https://ui.toast.com/posts/en_20220106
        # 1. Mouse click: mousedown -> mouseup -> click
        # 2. Touch click: touchstart -> touchend -> mousemove -> mousedown -> mouseup -> click
        # 3. Touch move:  touchstart -> touchmove -> touchend
        self.on("mousedown", self._mouse_down_event)
        self.on("touchstart", self._mouse_down_event)

        # Event modifiers
        # 1. Prevent checkbox default behavior
        # 2. Prevent propagation of the event
        self.on("mouseup.prevent", self._mouse_up_event)
        self.on("touchend.prevent", self._mouse_up_event)
        self.on("touchmove", self._mouse_move_event)

    def _update_icons(self):
        if self.skipped:
            self.props(f'checked-icon="{self.skipped_icon}" unchecked-icon="{self.skipped_icon}" keep-color')
        else:
            self.props(f'checked-icon="{self.checked_icon}" unchecked-icon="{self.unchecked_icon}" keep-color')

    def _update_style(self, value: bool | None):
        if value is None:  # Skipped state
            self.value = True  # Keep checkbox checked for skipped state
            self.skipped = True
            self.props("color=grey-8")
        else:
            self.value = value
            self.skipped = False
            self.props("color=currentColor" if value else "color=grey-8")
        
        self._update_icons()
            
        # Update habit name color
        # Get the start and end of the current week
        week_start = self.day - datetime.timedelta(days=self.day.weekday())
        week_end = week_start + datetime.timedelta(days=6)
        # Count ticks for current week (don't count skipped days)
        week_ticks = sum(1 for day in self.habit.ticked_days 
                        if week_start <= day <= week_end)
        
        # Check if this habit is skipped today
        is_skipped_today = (
            self.day == datetime.date.today() and 
            self.habit.record_by(self.day) and 
            self.habit.record_by(self.day).done is None
        )
        
        ui.run_javascript(f"""
        if (window.updateHabitColor) {{
            window.updateHabitColor(
                '{self.habit.id}', 
                {self.habit.weekly_goal or 0}, 
                {week_ticks},
                {str(is_skipped_today).lower()}
            );
        }}
        """)

    async def _mouse_down_event(self, e):
        logger.info(f"Down event: {self.day}, {e.args.get('type')}")
        self.hold.clear()
        self.moving = False
        try:
            async with asyncio.timeout(0.2):
                await self.hold.wait()
        except asyncio.TimeoutError:
            value = await note_tick(self.habit, self.day)
            if value is not None:
                self._update_style(value)
        else:
            if self.moving:
                logger.info("Mouse moving, skip...")
                return
            # Cycle through states: unchecked -> checked -> skipped -> unchecked
            if not self.value:  # Currently unchecked
                value = True  # Move to checked
            elif not self.skipped:  # Currently checked, not skipped
                value = None  # Move to skipped
            else:  # Currently skipped
                value = False  # Move to unchecked
                
            self._update_style(value)
            # Do update completion status
            await habit_tick(self.habit, self.day, value)
            # Update local state only
            self._update_style(value)

    async def _mouse_up_event(self, e):
        logger.info(f"Up event: {self.day}, {e.args.get('type')}")
        self.hold.set()

    async def _mouse_move_event(self):
        self.moving = True
        self.hold.set()


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
        if len(value) > 30:
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


class HabitAddButton:
    def __init__(self, habit_list: HabitList, refresh: Callable, list_options: list[dict]) -> None:
        self.habit_list = habit_list
        self.refresh = refresh
        
        with ui.column().classes("w-full gap-2"):
            with ui.row().classes("w-full items-center gap-2"):
                self.name_input = ui.input("New habit name").props('dense outlined')
                self.name_input.classes("flex-grow")
                
                self.goal_input = ui.number(min=0, max=7).props('dense outlined')
                self.goal_input.style("width: 120px")
                
                # Create name-to-id mapping for list selector
                self.name_to_id = {"No List": None}
                self.name_to_id.update({opt["label"]: opt["value"] for opt in list_options[1:]})
                
                # Use just the names as options
                options = list(self.name_to_id.keys())
                
                self.list_select = ui.select(
                    options=options,
                    value="No List",
                ).props('dense outlined options-dense')
                self.list_select.style("width: 150px")
            
            with ui.row().classes("w-full justify-end"):
                ui.button("Add Habit", on_click=self._async_task).props("unelevated")
            
        # Keep enter key functionality
        self.name_input.on("keydown.enter", self._async_task)
        self.goal_input.on("keydown.enter", self._async_task)

    async def _async_task(self):
        if not self.name_input.value:
            return
        await self.habit_list.add(self.name_input.value)
        # Set weekly goal and list after habit is created
        habits = self.habit_list.habits
        if habits:
            habits[-1].weekly_goal = self.goal_input.value or 0  # Default to 0 if empty
            habits[-1].list_id = self.name_to_id[self.list_select.value]
            logger.info(f"Set weekly goal to {habits[-1].weekly_goal}")
            logger.info(f"Set list to {habits[-1].list_id}")
        logger.info(f"Added new habit: {self.name_input.value}")
        self.refresh()
        self.name_input.set_value("")
        self.goal_input.set_value(None)
        self.list_select.set_value(None)


TODAY = "today"


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

        self.classes("inline-block w-14")  # w-14 = width: 56px
        self.props("dense")
        unchecked_icon, checked_icon = self._icon_svg()
        self.props(f'unchecked-icon="{unchecked_icon}"')
        self.props(f'checked-icon="{checked_icon}"')

        if is_bind_data:
            self.bind_value(self, "value")  # Bind to local value

    @property
    def ticked(self) -> bool | None:
        record = self.habit.ticked_data.get(self.day)
        return record.done if record else False

    def _icon_svg(self):
        unchecked_color, checked_color = "rgb(54,54,54)", "rgb(103,150,207)"
        # Use Chartreuse color for today's number
        text_color = "chartreuse" if self.day == datetime.date.today() else "white"
        return (
            icons.SQUARE.format(color=unchecked_color, text=self.day.day, text_color=text_color),
            icons.SQUARE.format(color=checked_color, text=self.day.day, text_color=text_color),
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


def habit_notes(records: List[CheckedRecord], limit: int = 10):
    with ui.timeline(side="right").classes("w-full pt-5 px-3 whitespace-pre-line"):
        for record in records[:limit]:
            color = "primary" if record.done else "grey-8"
            ui.timeline_entry(
                record.text,
                title="title",
                subtitle=record.day.strftime("%B %d, %Y"),
                color=color,
            )
