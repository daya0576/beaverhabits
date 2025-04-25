import asyncio
import calendar
import datetime
import os
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Optional, Self

from dateutil.relativedelta import relativedelta
from nicegui import app, events, ui
from nicegui.elements.button import Button

from beaverhabits.accessibility import index_badge_alternative_text
from beaverhabits.configs import TagSelectionMode, settings
from beaverhabits.core.backup import backup_to_telegram
from beaverhabits.core.completions import CStatus, get_habit_date_completion
from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.plan import plan
from beaverhabits.storage.dict import DAY_MASK, MONTH_MASK
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import (
    EVERY_DAY,
    Backup,
    CheckedRecord,
    Habit,
    HabitFrequency,
    HabitList,
    HabitStatus,
)
from beaverhabits.utils import (
    PERIOD_TYPE,
    PERIOD_TYPES,
    PERIOD_TYPES_FOR_HUMAN,
    WEEK_DAYS,
    D,
    M,
    W,
    Y,
    ratelimiter,
)

strptime = datetime.datetime.strptime

DAILY_NOTE_MAX_LENGTH = 1000
CALENDAR_EVENT_MASK = "%Y/%m/%d"


def redirect(x):
    ui.navigate.to(os.path.join(get_root_path(), x))


def open_tab(x):
    ui.navigate.to(os.path.join(get_root_path(), x), new_tab=True)


def link(text: str, target: str, color: str = "text-white") -> ui.link:
    return ui.link(text, target=target).classes(
        f"dark:{color} no-underline hover:no-underline"
    )


def menu_header(title: str, target: str):
    link = ui.link(title, target=target)
    link.classes(
        "text-semibold text-2xl dark:text-white no-underline hover:no-underline"
    )
    link.props('role="heading" aria-level="1" aria-label="Go to home page"')
    return link


def menu_icon_button(
    icon_name: str, click: Optional[Callable] = None, tooltip: str | None = None
) -> Button:
    button = ui.button(icon=icon_name, color=None, on_click=click)
    button.props("flat=true unelevated=true padding=xs backgroup=none")
    if tooltip:
        button = button.tooltip(tooltip)

    # Accessibility
    button.props('aria-haspopup="true" aria-label="menu"')

    return button


def menu_icon_item(*args, **kwargs):
    menu_item = ui.menu_item(*args, **kwargs).classes("items-center")
    # Accessibility
    return menu_item.props('dense role="menuitem"')


def habit_tick_dialog(record: CheckedRecord | None):
    text = record.text if record else ""
    with ui.dialog() as dialog, ui.card().props("flat") as card:
        dialog.props('backdrop-filter="blur(4px)"')
        card.classes("w-[640px]")

        with ui.column().classes("gap-0 w-full"):
            t = ui.textarea(
                label="Note",
                value=text,
                validation={
                    "Too long!": lambda value: len(value) < DAILY_NOTE_MAX_LENGTH
                },
            )
            t.classes("w-full")
            # t.props("autogrow")

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
async def habit_tick(habit: Habit, day: datetime.date, value: bool):
    # Avoid duplicate tick
    record = habit.record_by(day)
    if record and record.done == value:
        return

    # Transaction start
    await habit.tick(day, value)
    logger.info(f"Day {day} ticked: {value}")


class HabitCheckBox(ui.checkbox):
    def __init__(
        self,
        status: list[CStatus],
        habit: Habit,
        today: datetime.date,
        day: datetime.date,
        refresh: Callable | None = None,
    ) -> None:
        self.habit = habit
        self.day = day
        self.today = today
        self.status = status
        value = CStatus.DONE in status
        self.refresh = refresh
        super().__init__("", value=value)
        self._update_style(value)

        # Hold on event flag
        self.hold = asyncio.Event()
        self.moving = False

        # Click Event
        self.on("click", self._click_event)

        # Touch and hold event
        # Sequence of events: https://ui.toast.com/posts/en_20220106
        # 1. Mouse click: mousedown -> mouseup -> click
        # 2. Touch click: touchstart -> touchend -> mousemove -> mousedown -> mouseup -> click
        # 3. Touch move:  touchstart -> touchmove -> touchend
        self.on("mousedown", self._mouse_down_event)
        self.on("touchstart", self._mouse_down_event)

        # Event modifiers
        # 1. *Prevent* checkbox default behavior
        # 2. *Prevent* propagation of the event
        self.on("mouseup", self._mouse_up_event)
        self.on("touchend", self._mouse_up_event)
        self.on("touchmove", self._mouse_move_event)
        # self.on("mousemove", self._mouse_move_event)

        # Checklist: value change, scrolling
        # - Desktop browser
        # - iOS browser / standalone mode
        # - Android browser / PWA

    def _refresh(self):
        logger.debug(f"Refresh: {self.day}, {self.value}")
        if not self.refresh:
            return
        if not self.habit.period:
            return

        # Do refresh the components
        self.refresh()

    async def _mouse_down_event(self, e):
        logger.info(f"Down event: {self.day}, {e.args.get('type')}")
        self.hold.clear()
        self.moving = False
        try:
            async with asyncio.timeout(0.25):
                await self.hold.wait()
        except asyncio.TimeoutError:
            # Long press diaglog
            value = await note_tick(self.habit, self.day)

            if value is not None:
                self.value = value
                self._refresh()

            await self._blur()

    async def _click_event(self, e):
        self.value = e.sender.value

        # Do update completion status
        await habit_tick(self.habit, self.day, self.value)

        self._refresh()

    async def _mouse_up_event(self, e):
        logger.info(f"Up event: {self.day}, {e.args.get('type')}")
        self.hold.set()

    async def _mouse_move_event(self):
        # logger.info(f"Move event: {self.day}, {e}")
        self.moving = True
        self.hold.set()

    async def _blur(self):
        # Resolve ripple issue
        # https://github.com/quasarframework/quasar/blob/dev/ui/src/components/checkbox/QCheckbox.sass
        await ui.run_javascript(
            """
           const checkboxes = document.querySelectorAll('.q-checkbox');
           checkboxes.forEach(checkbox => {checkbox.blur()});
           """
        )

    def _update_style(self, value: bool):
        self.value = value

        # Accessibility
        days = (self.today - self.day).days
        if days == 0:
            self.props('aria-label="Today"')
        elif days == 1:
            self.props('aria-label="Yesterday"')
        else:
            self.props(f'aria-label="{days} days ago"')

        # icons, e.g. sym_o_notes
        checked, unchecked = icons.DONE, icons.CLOSE
        if self.habit.period:
            checked = icons.DONE_ALL
            if CStatus.PERIOD_DONE in self.status:
                unchecked = icons.DONE

        self.props(f'checked-icon="{checked}" unchecked-icon="{unchecked}" keep-color')


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
    def __init__(self, habit: Habit, label: str = "") -> None:
        super().__init__(value=self.encode_name(habit), label=label)
        self.habit = habit
        self.validation = self._validate
        self.props("dense hide-bottom-space")

        self.on("blur", self._on_blur)
        self.on("keydown.enter", self._on_keydown_enter)

    async def _on_keydown_enter(self):
        await self._save(self.value)
        ui.notify("Habit name saved")

    async def _on_blur(self):
        await self._save(self.value)

    async def _save(self, value: str):
        name, tags = self.decode_name(value)
        self.habit.name = name
        self.habit.tags = tags
        logger.info(f"Habit Name changed to {name}")
        logger.info(f"Habit Tags changed to {tags}")
        self.value = self.encode_name(self.habit)

    def _validate(self, value: str) -> Optional[str]:
        if not value:
            return "Name is required"
        if len(value) > 50:
            return "Too long"

    @staticmethod
    def encode_name(habit: Habit) -> str:
        name = habit.name
        if habit.tags:
            tags = [f"#{tag}" for tag in habit.tags]
            name = f"{name} {' '.join(tags)}"

        return name

    @staticmethod
    def decode_name(name: str) -> tuple[str, list[str]]:
        if "#" not in name:
            return name, []

        tokens = name.split("#")
        return tokens[0].strip(), [x.strip() for x in tokens[1:]]


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
        # Check premium plan
        if await plan.habit_limit_reached(self.habit_list):
            return

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
        refreshs: list[Callable] | None = None,
    ) -> None:
        self.today = today
        self.habit = habit
        self.refreshs = refreshs
        super().__init__(self._tick_days, on_change=self._async_task)

        self.props("multiple minimal flat today-btn")
        self.props(f"default-year-month={self.today.strftime(MONTH_MASK)}")
        self.props(f"first-day-of-week='{(settings.FIRST_DAY_OF_WEEK + 1) % 7}'")

        self.classes("shadow-none")

        # self.bind_value_from(self, "_tick_days")
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

        if self.refreshs:
            logger.debug("refresh page")
            for refresh in self.refreshs:
                refresh()


@dataclass
class CalendarHeatmap:
    """Habit records by weeks"""

    today: datetime.date

    headers: list[str]
    data: list[list[datetime.date]]
    week_days: list[str]

    @property
    def first_day(self) -> datetime.date:
        return self.data[0][0]

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
        status: list[CStatus],
        readonly: bool = False,
        refresh: Callable | None = None,
    ) -> None:
        self.habit = habit
        self.day = day
        self.status = status
        self.refresh = refresh
        super().__init__("", value=self.ticked)

        self.classes("inline-block")
        self.props("dense")
        unchecked_icon, checked_icon = self._icon_svg()
        self.props(f'unchecked-icon="{unchecked_icon}"')
        self.props(f'checked-icon="{checked_icon}"')

        self.on_value_change(self._async_task)
        if readonly:
            self.on("mousedown.prevent", lambda: True)
            self.on("touchstart.prevent", lambda: True)

    @property
    def ticked(self) -> bool:
        record = self.habit.ticked_data.get(self.day)
        return bool(record and record.done)

    def _icon_svg(self):
        unchecked_color, checked_color = "rgb(54,54,54)", icons.PRIMARY_COLOR
        if CStatus.PERIOD_DONE in self.status:
            # Normalization + Linear Interpolation
            unchecked_color = "rgb(40,87,141)"
        return (
            icons.SQUARE.format(color=unchecked_color, text=self.day.day),
            icons.SQUARE.format(color=checked_color, text=self.day.day),
        )

    async def _async_task(self, e: events.ValueChangeEventArguments):
        # Update persistent storage
        await self.habit.tick(self.day, e.value)
        logger.info(f"Day {self.day} ticked: {e.value}")

        if self.refresh:
            logger.debug("refresh page")
            self.refresh()


@ui.refreshable
def habit_heat_map(
    habit: Habit,
    calendar: CalendarHeatmap,
    readonly: bool = False,
    refresh: Callable | None = None,
):
    today = calendar.today

    # Habit completions
    status_map = get_habit_date_completion(habit, calendar.first_day, today)

    with ui.column().classes("gap-0"):
        # Headers
        with ui.row(wrap=False).classes("gap-0"):
            for header in calendar.headers:
                header_lable = ui.label(header).classes("text-gray-300 text-center")
                header_lable.style("width: 20px; line-height: 18px; font-size: 9px;")
            ui.label().style("width: 22px;")

        # Day matrix
        for i, weekday_days in enumerate(calendar.data):
            with ui.row(wrap=False).classes("gap-0"):
                for day in weekday_days:
                    if day <= calendar.today:
                        status = status_map.get(day, [])
                        CalendarCheckBox(habit, day, status, readonly, refresh=refresh)
                    else:
                        ui.label().style("width: 20px; height: 20px;")

                week_day_abbr_label = ui.label(calendar.week_days[i])
                week_day_abbr_label.classes("indent-1.5 text-gray-300")
                week_day_abbr_label.style(
                    "width: 22px; line-height: 20px; font-size: 9px;"
                )


def grid(columns: int, rows: int | None = 1) -> ui.grid:
    return ui.grid(columns=columns, rows=rows).classes("gap-0 items-center")


@ui.refreshable
def habit_history(today: datetime.date, habit: Habit, total_months: int = 13):
    # get lastest 6 months, e.g. Feb
    months, data = [], []
    for i in range(total_months, 0, -1):
        offset_date = today - relativedelta(months=i)
        months.append(offset_date.strftime("%b"))

        count = sum(
            1
            for x in habit.ticked_days
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
                    "itemStyle": {"color": icons.PRIMARY_COLOR},
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
    def __init__(self, today: datetime.date, habit: Habit) -> None:
        super().__init__(habit)
        self.props("color=grey-9 rounded transparent")
        self.style("font-size: 80%; font-weight: 500")

        # Accessibility
        ticked_days = habit.ticked_days
        self.props(
            f' tabindex="0" '
            f'aria-label="total completion: {len(ticked_days)};'
            f'{index_badge_alternative_text(today, habit)}"'
        )


class HabitTag(ui.chip):
    def __init__(self, tag_name: str) -> None:
        super().__init__(
            text=tag_name,
            color="oklch(0.3 0 0)",
            text_color="oklch(0.85 0 0)",
            selected=tag_name in TagManager.get_all(),
        )

        # https://tailwindcss.com/docs/colors
        self.props("dense")
        self.style("font-size: 80%; font-weight: 500")
        self.style("padding: 8px 9px")
        self.style("margin: 0px 2px")


def habit_notes(habit: Habit, limit: int = 10):
    notes = [x for x in habit.records if x.text]
    notes.sort(key=lambda x: x.day, reverse=True)

    with ui.timeline(side="right").classes("w-full pt-5 px-3 whitespace-pre-line"):
        for record in notes[:limit]:
            text = record.text
            # text = record.text.replace(" ", "&nbsp;")
            color = "primary" if record.done else "grey-8"
            with ui.timeline_entry(
                body=text,
                subtitle=record.day.strftime("%B %d, %Y"),
                color=color,
            ) as entry:
                # https://github.com/zauberzeug/nicegui/wiki/FAQs#why-do-all-my-elements-have-the-same-value
                entry.on("dblclick", lambda _, d=record.day: note_tick(habit, d))


def habit_streak(today: datetime.date, habit: Habit):
    status = get_habit_date_completion(habit, today.replace(year=today.year - 1), today)
    dates = sorted(status.keys(), reverse=True)
    if len(dates) <= 1:
        return

    # find the streaks of the dates
    months, data = [], []
    streak_count = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == -1:
            streak_count += 1
        else:
            months.insert(0, dates[i - 1])
            data.insert(0, streak_count)
            streak_count = 1
            if len(months) >= 5:
                break
    else:
        months.insert(0, dates[-1])
        data.insert(0, streak_count)

    # draw the graph
    months = [x.strftime("%d/%m") for x in months]

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
                    "type": "bar",
                    "data": data,
                    "itemStyle": {"color": icons.PRIMARY_COLOR},
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


class TagManager:
    @staticmethod
    def get_all() -> set[str]:
        try:
            return set(app.storage.user.get("index_tags_filter", []))
        except Exception as e:
            logger.error(f"Failed to get tags: {e}")
            return set()

    @staticmethod
    def add(tag: str) -> None:
        if settings.TAG_SELECTION_MODE == TagSelectionMode.SINGLE:
            app.storage.user["index_tags_filter"] = [tag]
        else:
            tags = set(TagManager.get_all())
            tags.add(tag)
            app.storage.user["index_tags_filter"] = list(tags)

    @staticmethod
    def remove(tag: str) -> None:
        tags = set(TagManager.get_all())
        if tag not in tags:
            logger.warning(f"Tag {tag} not found")

        tags.remove(tag)
        app.storage.user["index_tags_filter"] = list(tags)


def get_all_tags(habits: list[Habit]) -> list[str]:
    result = []
    for habit in habits:
        for tag in habit.tags:
            if tag not in result:
                result.append(tag)
    return result


def tag_filter_component(active_habits: list[Habit], refresh: Callable):
    all_tags = get_all_tags(active_habits)
    if not all_tags:
        return

    # display components
    with ui.row().classes("gap-0.5 justify-right w-80"):
        for tag_name in all_tags:
            TagChip(tag_name, refresh=refresh)
        TagChip("Others", refresh=refresh)


def habits_by_tags(active_habits: list[Habit]) -> dict[str, list[Habit]]:
    all_tags = get_all_tags(active_habits)
    if not all_tags:
        return {"": active_habits}

    all_tags.append("Others")

    habits = OrderedDict()
    # with tags
    for habit in active_habits:
        for tag in habit.tags:
            habits.setdefault(tag, []).append(habit)
    # without tags
    habits["Others"] = [h for h in active_habits if not h.tags]

    selected_tags = TagManager.get_all() & set(all_tags)
    if selected_tags:
        habits = OrderedDict(
            (key, value) for key, value in habits.items() if key in selected_tags
        )

    return habits


class TagChip(ui.chip):
    def __init__(
        self, tag_name: str, refresh: Callable | None = None, selectable=True
    ) -> None:
        super().__init__(
            text=tag_name,
            color="oklch(0.27 0 0)",
            text_color="oklch(0.9 0 0)",
            selectable=selectable,
            selected=tag_name in TagManager.get_all(),
        )

        # https://tailwindcss.com/docs/colors
        self.props("dense")
        self.style("font-size: 80%; font-weight: 500")
        self.style("padding: 8px 9px")
        self.style("margin: 0px 2px")

        self.on_click(self._async_task)
        self.refresh = refresh

    async def _async_task(self: Self):
        if self.selected:
            TagManager.add(self.text)
        else:
            TagManager.remove(self.text)

        if self.refresh:
            self.refresh()


def number_input(value: int, label: str):
    return ui.input(value=str(value), label=label).props("dense").classes("w-8")


def backup_input(label: str, value: str):
    backup_input = ui.input(label=label)
    backup_input.classes("w-full")
    if value:
        backup_input.value = value
    return backup_input


def habit_backup_dialog(habit_list: HabitList) -> ui.dialog:
    @plan.pro_required("Pro plan required to use backup feature")
    def set_backup():
        habit_list.backup = Backup(
            telegram_chat_id=chat_id_input.value,
            telegram_bot_token=bot_token_input.value,
        )
        ui.notify("Backup saved", color="positive")

    async def test_backup():
        bot_token = bot_token_input.value
        if not bot_token:
            ui.notify("Telegram Bot Token is empty", color="negative")
            return
        telegram_id = chat_id_input.value
        if not telegram_id:
            ui.notify("Telegram ID is empty", color="negative")
            return

        try:
            backup_to_telegram(bot_token, telegram_id, habit_list)
            ui.notify("Backup test success", color="positive")
        except Exception:
            logger.exception("Failed to send backup")
            ui.notify(f"Invalid Telegram ID: {telegram_id}", color="negative")

    with ui.dialog() as dialog, ui.card().props("flat") as card:
        dialog.props('backdrop-filter="blur(4px)"')
        card.classes("w-5/6 max-w-64")

        with ui.column().classes("w-full"):
            token, chat_id = (
                habit_list.backup.telegram_bot_token or "",
                habit_list.backup.telegram_chat_id or "",
            )
            bot_token_input = backup_input("Telegram Bot Token", token)
            chat_id_input = backup_input("Telegram Chat ID", chat_id)

            with ui.row():
                ui.button("Save").on_click(set_backup)
                ui.button("Test").on_click(test_backup)

    return dialog


def habit_edit_dialog(habit: Habit) -> ui.dialog:
    p = habit.period or EVERY_DAY

    def try_update_period() -> bool:
        p_count = period_count.value
        t_count = target_count.value

        if period_type.value not in PERIOD_TYPES:
            ui.notify("Invalid period type", color="negative")
            return False
        p_type: PERIOD_TYPE = period_type.value

        # Check value is digit
        if not p_count.isdigit() or not t_count.isdigit():
            ui.notify("Invalid interval", color="negative")
            return False
        p_count, t_count = int(p_count), int(t_count)
        if p_count <= 0 or t_count <= 0:
            ui.notify("Invalid period count", color="negative")
            return False

        # Check value is in range
        max_times = {D: 1, W: 7, M: 31, Y: 366}
        if t_count > max_times.get(p_type, 1) * p_count:
            ui.notify("Invalid interval", color="negative")
            return False

        habit.period = HabitFrequency(p_type, p_count, t_count)
        logger.info(f"Habit period changed to {habit.period}")
        dialog.close()

        # wildly reload the page
        ui.navigate.reload()

        return True

    def reset():
        period_type.value = EVERY_DAY.period_type
        period_count.value = str(EVERY_DAY.period_count)
        target_count.value = str(EVERY_DAY.target_count)

    with ui.dialog() as dialog, ui.card().props("flat") as card:
        dialog.props('backdrop-filter="blur(4px)"')
        card.classes("w-5/6 max-w-64")

        with ui.column().classes("w-full"):
            HabitNameInput(habit, label="Name").classes("w-full")

            # Habit Frequency
            with ui.row().classes("items-center"):
                target_count = number_input(p.target_count, label="Times")

                ui.label("/").classes("text-gray-300")

                period_count = number_input(value=p.period_count, label="Every")
                period_type = ui.select(
                    PERIOD_TYPES_FOR_HUMAN, value=p.period_type, label=" "
                ).props("dense")

            with ui.row():
                ui.button("Save", on_click=try_update_period).props("flat")
                ui.button("Reset", on_click=reset).props("flat")

    return dialog


def auth_header(text: str):
    with ui.row():
        ui.label(text).classes("text-3xl font-bold")

def auth_redirect(text: str, target: str):
    return link(text, target).classes("text-xs text-gray-950")

def auth_forgot_password(email_input: ui.input, reset: Callable):
    async def try_forgot_password():
        email = email_input.value
        if not email:
            ui.notify("Email is required", color="negative")
            return

        spinner.classes(remove="hidden")
        await reset(email)
        spinner.classes("hidden")

    forgot_entry = auth_redirect("Forgot password?", "#")
    forgot_entry.on("click", try_forgot_password)
    spinner = ui.spinner().classes("hidden")


def auth_email(value: str | None = None):
    email = ui.input("email").classes("w-full")
    if value:
        email.value = value
    return email


def auth_password(title: str = "Password", value: str | None = None):
    password = ui.input("password", password=True, password_toggle_button=True)
    password.classes("w-full")
    if value:
        password.value = value
    if title:
        password.label = title
    return password


@contextmanager
def auth_card(title: str, func: Callable):
    with ui.card().classes("absolute-center shadow-none w-80 sm:w-96"):
        with ui.column().classes("w-full gap-4"):
            auth_header(title)
            yield
            ui.button("Continue", on_click=func).props("dense").classes("w-full")
