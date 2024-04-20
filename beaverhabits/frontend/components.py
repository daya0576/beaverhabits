from contextlib import contextmanager
import datetime
from typing import Callable, Optional
from nicegui import events, ui
from nicegui.elements.button import Button

from beaverhabits.storage.dict import DAY_MASK
from beaverhabits.storage.storage import Habit, HabitList
from beaverhabits.frontend import icons
from beaverhabits.configs import settings
from beaverhabits.logging import logger

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
        self.props(
            f'checked-icon="{icons.STAR_FULL}" unchecked-icon="{icons.STAR}" keep-color color=grey-8'
        )
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


@contextmanager
def compat_card():
    row_compat_classes = "pl-4 pr-1 py-0"
    with ui.card().classes(row_compat_classes).classes("shadow-none"):
        yield


class HabitDateInput(ui.date):
    def __init__(self, habit: Habit) -> None:
        value = [day.strftime(DAY_MASK) for day in habit.ticked_days]
        super().__init__(value, on_change=self._async_task)
        self.props(f"multiple subtitle='{habit.name}'")
        self.props(f"first-day-of-week='{settings.FIRST_DAY_OF_WEEK}'")
        self.classes("shadow-none")
        self.habit = habit

    async def _async_task(self, e: events.ValueChangeEventArguments):
        old_values = set(self.habit.ticked_days)
        new_values = set(strptime(x, DAY_MASK).date() for x in e.value)

        for added_item in new_values - old_values:
            await self.habit.tick(added_item, True)
            logger.info(f"Day {added_item} ticked: True")
        for added_item in old_values - new_values:
            await self.habit.tick(added_item, False)
            logger.info(f"Day {added_item} ticked: False")
