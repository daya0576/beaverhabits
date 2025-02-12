import datetime
from enum import Enum
from typing import List as TypeList, Optional, Protocol, Self

from beaverhabits.app.db import User


class CheckedRecord(Protocol):
    @property
    def day(self) -> datetime.date: ...

    @property
    def done(self) -> bool | None: ...  # None means skipped

    @done.setter
    def done(self, value: bool | None) -> None: ...

    @property
    def text(self) -> str: ...

    @text.setter
    def text(self, value: str) -> None: ...

    def __str__(self):
        if self.done is None:
            return f"{self.day} [s]"  # skipped
        return f"{self.day} {'[x]' if self.done else '[ ]'}"

    __repr__ = __str__


class HabitStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archive"
    SOLF_DELETED = "soft_delete"

    @classmethod
    def all(cls) -> tuple:
        return tuple(cls.__members__.values())


class Habit[R: CheckedRecord](Protocol):
    @property
    def list_id(self) -> str | None: ...

    @list_id.setter
    def list_id(self, value: str | None) -> None: ...

    @property
    def id(self) -> str | int: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, value: str) -> None: ...

    @property
    def star(self) -> bool: ...

    @star.setter
    def star(self, value: int) -> None: ...

    @property
    def records(self) -> TypeList[R]: ...

    @property
    def status(self) -> HabitStatus: ...

    @status.setter
    def status(self, value: HabitStatus) -> None: ...

    @property
    def weekly_goal(self) -> int: ...

    @weekly_goal.setter
    def weekly_goal(self, value: int) -> None: ...

    @property
    def ticked_days(self) -> list[datetime.date]: ...

    @property
    def ticked_data(self) -> dict[datetime.date, R]: ...

    def record_by(self, day: datetime.date) -> Optional[R]:
        return self.ticked_data.get(day)

    async def tick(
        self, day: datetime.date, done: bool | None, text: str | None = None
    ) -> CheckedRecord: ...

    def __str__(self):
        return self.name

    __repr__ = __str__


class List[H: Habit](Protocol):
    @property
    def id(self) -> str: ...
    
    @property
    def name(self) -> str: ...
    
    @name.setter
    def name(self, value: str) -> None: ...
    
    @property
    def habits(self) -> TypeList[H]: ...




class HabitList[H: Habit](Protocol):

    @property
    def habits(self) -> TypeList[H]: ...

    @property
    def order(self) -> TypeList[str]: ...

    @order.setter
    def order(self, value: TypeList[str]) -> None: ...

    async def add(self, name: str) -> None: ...

    async def remove(self, item: H) -> None: ...

    async def get_habit_by(self, habit_id: str) -> Optional[H]: ...


class SessionStorage[L: HabitList[H], H: Habit](Protocol):
    def get_user_habit_list(self) -> Optional[L]: ...

    def save_user_habit_list(self, habit_list: L) -> None: ...


class UserStorage[L: HabitList[H], H: Habit](Protocol):
    async def get_user_habit_list(self, user: User) -> Optional[L]: ...
    async def save_user_habit_list(self, user: User, habit_list: L) -> None: ...
    async def merge_user_habit_list(self, user: User, other: L) -> L: ...

    async def get_user_lists(self, user: User) -> TypeList[List[H]]: ...
    async def add_list(self, user: User, name: str) -> List[H]: ...
    async def update_list(self, user: User, list_id: str, name: str) -> None: ...
    async def delete_list(self, user: User, list_id: str) -> None: ...


def get_week_ticks(habit: Habit, day: datetime.date) -> tuple[int, bool]:
    """Calculate the number of ticks and if there are any actions in the week containing the given day.
    Returns:
        tuple: (number of ticks, whether there are any actions (ticks or skips))
    """
    week_start = day - datetime.timedelta(days=day.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    ticks = 0
    has_actions = False
    
    for d in (week_start + datetime.timedelta(days=i) for i in range(7)):
        record = habit.record_by(d)
        if record:
            if record.done or record.done is None:  # Only count ticks and skips as actions
                has_actions = True
            if record.done:
                ticks += 1
    
    return ticks, has_actions

def get_habit_priority(habit: Habit, days: list[datetime.date]) -> int:
    """Calculate priority for sorting habits.
    Returns:
    - 0: no checks (first)
    - 1: partially checked (second)
    - 2: skipped today (third)
    - 3: completed weekly goal (last)
    """
    today = datetime.date.today()
    record = habit.record_by(today)
    week_ticks, has_actions = get_week_ticks(habit, today)
    is_skipped_today = record and record.done is None
    is_completed = habit.weekly_goal and week_ticks >= habit.weekly_goal

    # Check in ascending priority order
    if not has_actions:
        return 0  # No checks (first)
    if has_actions and not is_skipped_today and not is_completed:
        return 1  # Partially checked (second)
    if is_skipped_today:
        return 2  # Skipped today (third)
    return 3  # Completed (last)

class HabitListBuilder[H: Habit]:
    def __init__(self, habit_list: HabitList[H], days: list[datetime.date] | None = None):
        self.habit_list = habit_list
        self.days = days or [datetime.date.today()]  # Default to today if no days provided
        self.status_list = (
            HabitStatus.ACTIVE,
            HabitStatus.ARCHIVED,
        )

    def status(self, *status: HabitStatus) -> Self:
        self.status_list = status
        return self

    def build(self) -> TypeList[H]:
        # Deep copy the list
        habits = [x for x in self.habit_list.habits if x.status in self.status_list]

        # Get order if exists
        o = self.habit_list.order

        # Sort by multiple criteria
        habits.sort(key=lambda x: (
            HabitStatus.all().index(x.status),  # Status first
            get_habit_priority(x, self.days),  # Then by completion priority
            not x.star,  # Then by star (starred on top)
            x.name.lower(),  # Then by name
            o.index(str(x.id)) if o and str(x.id) in o else float("inf")  # Finally by manual order
        ))

        return habits
