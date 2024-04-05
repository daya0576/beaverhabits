import logging
from typing import Callable, Dict, List, Optional, Type, Union
from nicegui import events, ui
from nicegui.elements.button import Button

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList


def compat_menu(name: str, callback: Callable):
    return ui.menu_item(name, callback).classes("items-center")


def menu_icon_button(icon_name: str, click: Optional[Callable] = None) -> Button:
    button_props = "flat=true unelevated=true padding=xs backgroup=none"
    return ui.button(icon=icon_name, color=None).props(button_props)


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
        self.props(f'checked-icon="sym_r_done" unchecked-icon="sym_r_close" keep-color')
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

    async def _async_task(self, e: events.ValueChangeEventArguments):
        self.habit.name = e.value


class HabitDeleteButton(ui.button):
    def __init__(self, habit: Habit, habit_list: HabitList, refresh: Callable) -> None:
        super().__init__(on_click=self._async_task, icon="delete")
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

    async def _async_task(self):
        logging.info(f"Adding new habit: {self.value}")
        await self.habit_list.add(self.value)
        self.refresh()
        self.set_value("")


class HabitPrioritySelect(ui.select):
    def __init__(
        self,
        habit: Habit,
        habit_list: HabitList,
        options: Union[List, Dict],
        refresh: Callable,
    ) -> None:
        super().__init__(options, on_change=self._async_task, value=habit.priority)
        self.habit = habit
        self.habit_list = habit_list
        self.bind_value(habit, "priority")
        self.refresh = refresh

    async def _async_task(self, e: events.ValueChangeEventArguments):
        # self.habit.priority = e.value
        self.habit_list.sort()
        self.refresh()
