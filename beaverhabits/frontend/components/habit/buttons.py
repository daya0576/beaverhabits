from typing import Callable
from nicegui import ui, events

from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.storage.storage import Habit, HabitList, HabitStatus

class HabitSaveButton(ui.button):
    def __init__(self, habit: Habit, habit_list: HabitList, refresh: Callable) -> None:
        super().__init__(on_click=self._async_task, text="Save")
        self.habit = habit
        self.habit_list = habit_list
        self.refresh = refresh
        self.props("unelevated dense")

    async def _async_task(self):
        # Save the habit
        if hasattr(self.habit, 'save'):
            await self.habit.save()
            logger.info(f"Saved habit: {self.habit.name}")
            ui.notify(f"Saved {self.habit.name}")
            self.refresh()
            
            # Scroll to the saved habit
            ui.run_javascript(f"scrollToHabit('{self.habit.id}')")
        else:
            logger.error(f"Habit {self.habit.name} does not have a save method")
            ui.notify(f"Error saving {self.habit.name}", type="error")

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

        # Save the status change
        if hasattr(self.habit, 'save'):
            await self.habit.save()
            logger.info(f"Saved status change for: {self.habit.name}")

        self.refresh()
        
        # Scroll to the updated habit
        ui.run_javascript(f"scrollToHabit('{self.habit.id}')")

class HabitAddButton:
    def __init__(self, habit_list: HabitList, refresh: Callable, list_options: list[dict] = None) -> None:
        self.habit_list = habit_list
        self.refresh = refresh
        
        with ui.row().classes("w-full items-center gap-2"):
            self.name_input = ui.input("New habit name").props('dense outlined')
            self.name_input.classes("flex-grow")
            ui.button("Add Habit", on_click=self._async_task).props("unelevated")
            
        # Keep enter key functionality
        self.name_input.on("keydown.enter", self._async_task)

    async def _async_task(self):
        if not self.name_input.value:
            return
        logger.debug(f"Adding habit to list: {self.habit_list}")
        await self.habit_list.add(self.name_input.value)
        logger.debug(f"Habit list after add: {self.habit_list}")
        logger.info(f"Added new habit: {self.name_input.value}")
        
        # Get the new habit's ID (it's the last one in the list)
        habits = self.habit_list.habits
        if habits:
            new_habit_id = habits[-1].id
            # Refresh the UI
            self.refresh()
            # Scroll to the new habit
            ui.run_javascript(f"scrollToHabit('{new_habit_id}')")
        else:
            self.refresh()
            
        self.name_input.set_value("")
