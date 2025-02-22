import asyncio
import datetime
from typing import Callable

from nicegui import ui, events

from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.sql.models import Habit, CheckedRecord
from beaverhabits.app.crud import toggle_habit_check, get_habit_checks
from ..utils import ratelimiter

DAILY_NOTE_MAX_LENGTH = 300

def habit_tick_dialog(record: CheckedRecord | None):
    text = record.text if record and hasattr(record, 'text') else ""
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
    # Get current record
    records = await get_habit_checks(habit.id, habit.user_id)
    record = next((r for r in records if r.day == day), None)
    
    result = await habit_tick_dialog(record)
    if result is None:
        return

    yes, text = result
    if text and len(text) > DAILY_NOTE_MAX_LENGTH:
        ui.notify("Note is too long", color="negative")
        return

    record = await toggle_habit_check(habit.id, habit.user_id, day, text, True)  # Always set to checked when using notes
    
    # Highlight the updated habit
    ui.run_javascript(f"highlightHabit('{habit.id}')")
    
    return record.done if record else None

@ratelimiter(limit=30, window=30)
@ratelimiter(limit=10, window=1)
async def habit_tick(habit: Habit, day: datetime.date, value: bool | None):
    # Get current record
    records = await get_habit_checks(habit.id, habit.user_id)
    record = next((r for r in records if r.day == day), None)
    
    if record and record.done == value:  # Use == to handle None case correctly
        return

    # Toggle the habit check, preserving any existing note
    text = record.text if record and hasattr(record, 'text') else None
    await toggle_habit_check(habit.id, habit.user_id, day, text, value)
    
    # Highlight the updated habit
    ui.run_javascript(f"highlightHabit('{habit.id}')")

async def get_week_ticks(habit: Habit, today: datetime.date) -> tuple[int, int]:
    """Get the number of ticks for the current week."""
    records = await get_habit_checks(habit.id, habit.user_id)
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    week_ticks = sum(1 for record in records 
                    if week_start <= record.day <= week_end and record.done)
    total_ticks = sum(1 for record in records if record.done)
    return week_ticks, total_ticks

async def get_last_week_completion(habit: Habit, today: datetime.date) -> bool:
    """Check if the habit was completed last week."""
    records = await get_habit_checks(habit.id, habit.user_id)
    last_week_start = today - datetime.timedelta(days=today.weekday() + 7)
    last_week_end = last_week_start + datetime.timedelta(days=6)
    last_week_ticks = sum(1 for record in records 
                         if last_week_start <= record.day <= last_week_end and record.done)
    return last_week_ticks >= (habit.weekly_goal or 0)

class BaseHabitCheckBox(ui.checkbox):
    def __init__(self, habit: Habit, day: datetime.date, value: bool | None) -> None:
        # Initialize with the actual state
        super().__init__("", value=value if value is not None else False)
        self.habit = habit
        self.day = day
        self.skipped = value is False  # Track skipped state (False means skipped, None means not set)
        text_color = "chartreuse" if self.day == datetime.date.today() else settings.HABIT_COLOR_DAY_NUMBER
        self.unchecked_icon = icons.SQUARE.format(color="rgb(54,54,54)", text=self.day.day, text_color=text_color)
        self.checked_icon = icons.DONE
        self.skipped_icon = icons.CLOSE
        
        # Set up initial state
        self._update_icons()
        
        # Initialize state without async
        self.value = value if value is not None else False
        self.skipped = value is False  # False means skipped, None means not set
        
        # Update visual state
        if self.skipped:
            self.props("color=grey-8")
        else:
            self.props("color=currentColor" if self.value else "color=grey-8")
        
        # Hold on event flag
        self.hold = asyncio.Event()
        self.moving = False

    def _update_icons(self):
        if self.skipped:
            self.props(f'checked-icon="{self.skipped_icon}" unchecked-icon="{self.skipped_icon}" keep-color')
        elif self.value:
            self.props(f'checked-icon="{self.checked_icon}" unchecked-icon="{self.checked_icon}" keep-color')
        else:
            self.props(f'checked-icon="{self.unchecked_icon}" unchecked-icon="{self.unchecked_icon}" keep-color')

    async def _update_style(self, value: bool | None):
        # First update internal state
        if value is None:  # Not set state
            self.value = False  # Show empty icon
            self.skipped = False
        elif value is False:  # Skipped state
            self.value = True  # Show skipped icon
            self.skipped = True
        else:  # Checked state
            self.value = True
            self.skipped = False
        
        # Then update visual state
        if self.skipped:
            self.props("color=grey-8")
        else:
            self.props("color=currentColor" if self.value else "color=grey-8")
        
        self._update_icons()
            
        # Add a small delay to ensure habit state is updated
        await asyncio.sleep(0.1)
            
        # Get fresh records after state update
        records = await get_habit_checks(self.habit.id, self.habit.user_id)
        ticked_days = {record.day for record in records if record.done}
        if value:  # Add current day if it's being checked
            ticked_days.add(self.day)
        elif value is False:  # Remove current day if it's being unchecked
            ticked_days.discard(self.day)
            
        # Get ticks for current week and last week's completion status
        week_ticks, _ = await get_week_ticks(self.habit, self.day)
        last_week_complete = await get_last_week_completion(self.habit, self.day)
        
        # Check if this habit is skipped today
        today_record = next((r for r in records if r.day == datetime.date.today()), None)
        is_skipped_today = today_record and today_record.done is None
        
        # Update state directly without refreshing
        ui.run_javascript(f"updateHabitAttributes('{self.habit.id}', {self.habit.weekly_goal or 0}, {week_ticks}, {str(is_skipped_today).lower() if is_skipped_today is not None else 'null'}, {str(last_week_complete).lower()})")

    async def _mouse_down_event(self, e):
        self.hold.clear()
        self.moving = False
        try:
            async with asyncio.timeout(0.2):
                await self.hold.wait()
        except asyncio.TimeoutError:
            if settings.ENABLE_HABIT_NOTES:
                value = await note_tick(self.habit, self.day)
                if value is not None:
                    await self._update_style(value)
            else:
                # Skip note dialog, just toggle to checked state
                value = True
                await habit_tick(self.habit, self.day, value)
                await self._update_style(value)
        else:
            if self.moving:
                return
            # Get current state from database
            records = await get_habit_checks(self.habit.id, self.habit.user_id)
            record = next((r for r in records if r.day == self.day), None)
            current_state = record.done if record else None
            
            # Determine next state based on current database state
            if current_state is None:  # Currently not set
                value = True  # Move to checked
            elif current_state:  # Currently checked
                value = False  # Move to skipped
            else:  # Currently skipped
                value = None  # Move to not set
            
            # Do update completion status
            await habit_tick(self.habit, self.day, value)
            # Update local state with latest data
            await self._update_style(value)

    async def _mouse_up_event(self, e):
        self.hold.set()

    async def _mouse_move_event(self):
        self.moving = True
        self.hold.set()

class HabitCheckBox(BaseHabitCheckBox):
    def __init__(self, habit: Habit, day: datetime.date, value: bool | None, refresh: Callable | None = None) -> None:
        super().__init__(habit, day, value)
        self.refresh = refresh

        # Event handlers
        self.on("mousedown", self._mouse_down_event)
        self.on("touchstart", self._mouse_down_event)
        self.on("mouseup.prevent", self._mouse_up_event)
        self.on("touchend.prevent", self._mouse_up_event)
        self.on("touchmove", self._mouse_move_event)

class HabitStarCheckbox(ui.checkbox):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__("", value=habit.star)
        self.habit = habit
        self.refresh = refresh
        self.props("dense fab-mini color=yellow-8")
        self.props('checked-icon="star" unchecked-icon="star_outline" size="sm"')
        self.on("change", self._async_task)

    async def _async_task(self, e):
        self.habit.star = e.value
        
        self.refresh()
        
        # Highlight the updated habit
        ui.run_javascript(f"highlightHabit('{self.habit.id}')")

class CalendarCheckBox(BaseHabitCheckBox):
    def __init__(
        self,
        habit: Habit,
        day: datetime.date,
        today: datetime.date,
        initial_value: bool | None = False,
    ) -> None:
        # Pass the initial value to super()
        super().__init__(habit, day, initial_value)
        self.today = today
        
        self.classes("inline-block w-14")  # w-14 = width: 56px
        self.props("dense")
        
        # Event handlers
        self.on("mousedown", self._mouse_down_event)
        self.on("touchstart", self._mouse_down_event)
        self.on("mouseup.prevent", self._mouse_up_event)
        self.on("touchend.prevent", self._mouse_up_event)
        self.on("touchmove", self._mouse_move_event)
        self.on("click.prevent", lambda _: None)  # Prevent default click behavior
        self.on("change.prevent", lambda _: None)  # Prevent default change behavior

    @classmethod
    async def create(
        cls,
        habit: Habit,
        day: datetime.date,
        today: datetime.date,
    ) -> 'CalendarCheckBox':
        """Factory method to create a CalendarCheckBox with async initialization."""
        # Get initial state
        records = await get_habit_checks(habit.id, habit.user_id)
        record = next((r for r in records if r.day == day), None)
        initial_value = record.done if record else None  # None means not set
        
        # Create instance with initial value
        return cls(habit, day, today, initial_value)
