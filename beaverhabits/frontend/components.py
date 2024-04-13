from contextlib import contextmanager
import logging
from typing import Callable, Dict, List, Optional, Type, Union
from nicegui import events, ui
from nicegui.elements.button import Button

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList
from beaverhabits.frontend import icons


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
        record: CheckedRecord,
        text: str = "",
        *,
        value: bool = False,
    ) -> None:
        super().__init__(text, value=value, on_change=self._async_task)
        self.habit = habit
        self.record = record
        self._update_style(value)
        self.bind_value(record, "done")

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
        await self.habit.tick(self.record)


class HabitNameInput(ui.input):
    def __init__(self, habit: Habit) -> None:
        super().__init__(value=habit.name, on_change=self._async_task)
        self.habit = habit
        self.validation = lambda value: "Too long" if len(value) > 18 else None
        self.props("dense")

    async def _async_task(self, e: events.ValueChangeEventArguments):
        self.habit.name = e.value


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


class HabitDeleteButton(ui.button):
    def __init__(self, habit: Habit, habit_list: HabitList, refresh: Callable) -> None:
        super().__init__(on_click=self._async_task, icon=icons.DELETE)
        self.habit = habit
        self.habit_list = habit_list
        self.refresh = refresh

    async def _async_task(self):
        await self.habit_list.remove(self.habit)
        self.refresh()


class HabitAddButton(ui.input):
    def __init__(self, habit_list: HabitList, refresh: Callable) -> None:
        super().__init__("New item")
        self.habit_list = habit_list
        self.refresh = refresh
        self.on("keydown.enter", self._async_task)
        self.props("dense")

    async def _async_task(self):
        logging.info(f"Adding new habit: {self.value}")
        await self.habit_list.add(self.value)
        self.refresh()
        self.set_value("")


@contextmanager
def compat_card():
    row_compat_classes = "pl-4 pr-1 py-0"
    with ui.card().classes(row_compat_classes).classes("shadow-none"):
        yield
