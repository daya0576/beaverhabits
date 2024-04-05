import datetime
import enum
from typing import List, Optional, Protocol


from beaverhabits.app.db import User


class CheckedRecord(Protocol):
    @property
    def day(self) -> datetime.date: ...

    @property
    def done(self) -> bool: ...

    @done.setter
    def done(self, value: bool) -> None: ...

    def __str__(self):
        return f"{self.day} {'[x]' if self.done else '[ ]'}"

    __repr__ = __str__


class Priority(enum.Enum):
    P1 = 1
    P2 = 2
    P3 = 3
    P4 = 4
    NONE = 100


class Habit[R: CheckedRecord](Protocol):
    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, value: str) -> None: ...

    @property
    def priority(self) -> int: ...

    @priority.setter
    def priority(self, value: int) -> None: ...

    @property
    def records(self) -> List[R]: ...

    def get_records_by_days(self, days: List[datetime.date]) -> List[R]: ...

    async def tick(self, record: R) -> None: ...

    def __str__(self):
        return self.name

    __repr__ = __str__


class HabitList[H: Habit](Protocol):
    @property
    def habits(self) -> List[H]: ...

    async def add(self, name: str) -> None: ...

    async def remove(self, item: H) -> None: ...

    def sort(self) -> None: ...


class SessionStorage[L: HabitList](Protocol):
    def get_user_habit_list(self) -> Optional[L]: ...

    def save_user_habit_list(self, habit_list: L) -> None: ...


class UserStorage[L: HabitList](Protocol):
    def get_user_habit_list(self, user: User) -> Optional[L]: ...

    def save_user_habit_list(self, user: User, habit_list: L) -> None: ...
