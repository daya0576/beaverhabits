import datetime
from enum import Enum
from typing import List, Optional, Protocol, Self

from beaverhabits.app.db import User


class CheckedRecord(Protocol):
    @property
    def day(self) -> datetime.date: ...

    @property
    def done(self) -> bool: ...

    @done.setter
    def done(self, value: bool) -> None: ...

    @property
    def text(self) -> str: ...

    @text.setter
    def text(self, value: str) -> None: ...

    def __str__(self):
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
    def records(self) -> List[R]: ...

    @property
    def status(self) -> HabitStatus: ...

    @status.setter
    def status(self, value: HabitStatus) -> None: ...

    @property
    def note(self) -> bool: ...

    @note.setter
    def note(self, value: bool) -> None: ...

    @property
    def ticked_days(self) -> list[datetime.date]:
        return [r.day for r in self.records if r.done]

    @property
    def ticked_records(self) -> dict[datetime.date, R]:
        return {r.day: r for r in self.records if r.done}

    async def tick(
        self, day: datetime.date, done: bool, text: str | None = None
    ) -> CheckedRecord: ...

    def __str__(self):
        return self.name

    __repr__ = __str__


class HabitList[H: Habit](Protocol):

    @property
    def habits(self) -> List[H]: ...

    @property
    def order(self) -> List[str]: ...

    @order.setter
    def order(self, value: List[str]) -> None: ...

    async def add(self, name: str) -> None: ...

    async def remove(self, item: H) -> None: ...

    async def get_habit_by(self, habit_id: str) -> Optional[H]: ...


class SessionStorage[L: HabitList](Protocol):
    def get_user_habit_list(self) -> Optional[L]: ...

    def save_user_habit_list(self, habit_list: L) -> None: ...


class UserStorage[L: HabitList](Protocol):
    async def get_user_habit_list(self, user: User) -> Optional[L]: ...

    async def save_user_habit_list(self, user: User, habit_list: L) -> None: ...

    async def merge_user_habit_list(self, user: User, other: L) -> L: ...


class HabitListBuilder:
    def __init__(self, habit_list: HabitList):
        self.habit_list = habit_list
        self.status_list = (
            HabitStatus.ACTIVE,
            HabitStatus.ARCHIVED,
        )

    def status(self, *status: HabitStatus) -> Self:
        self.status_list = status
        return self

    def build(self) -> List[Habit]:
        # Deep copy the list
        habits = [x for x in self.habit_list.habits if x.status in self.status_list]

        # sort by order
        if o := self.habit_list.order:
            habits.sort(
                key=lambda x: (o.index(str(x.id)) if str(x.id) in o else float("inf"))
            )

        # sort by star
        habits.sort(key=lambda x: x.star, reverse=True)

        # Sort by status
        all_status = HabitStatus.all()
        habits.sort(key=lambda x: all_status.index(x.status))

        return habits
