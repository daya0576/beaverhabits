import asyncio
from typing import Any, Callable, Dict, List, Optional, Union
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
        if self.record not in self.habit.records:
            self.habit.records.append(self.record)


class HabitPrioritySelect(ui.select):
    def __init__(
        self,
        habit: Habit,
        habit_list: HabitList,
        options: Union[List, Dict],
        value: Any = None,
    ) -> None:
        super().__init__(options, on_change=self._async_task, value=value)
        self.habit = habit
        self.habit_list = habit_list
        self.bind_value(habit, "priority")

    async def _async_task(self, e: events.ValueChangeEventArguments):
        await self.habit.update_priority(e.value)
        # await asyncio.sleep(5)
        # ui.notify(f"Asynchronous task started: {self.habit}")
        self.habit_list.sort()
