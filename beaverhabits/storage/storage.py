import abc
from dataclasses import dataclass, field
import datetime
from typing import Callable, List, Optional, OrderedDict


from beaverhabits.app.db import User


@dataclass
class CheckedRecord(abc.ABC):
    day: datetime.date
    done: bool

    def __str__(self):
        return f"{self.day} {'[x]' if self.done else '[ ]'}"

    __repr__ = __str__


@dataclass
class Habit(abc.ABC):
    name: str
    priority: int = 2
    records: List[CheckedRecord] = field(default_factory=list)

    def get_records_by_date(
        self, days: List[datetime.date]
    ) -> OrderedDict[datetime.date, CheckedRecord]:
        all_records_by_date = OrderedDict(
            (x, CheckedRecord(day=x, done=False)) for x in days
        )
        for x in self.records:
            all_records_by_date[x.day] = x
        return all_records_by_date

    @abc.abstractmethod
    def tick(self, record: CheckedRecord) -> None:
        ...

    @abc.abstractmethod
    async def update_priority(self, priority: int) -> None:
        ...

    def __str__(self):
        return self.name

    __repr__ = __str__


@dataclass
class HabitList(abc.ABC):
    items: List[Habit] = field(default_factory=list)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    on_change: Optional[Callable[[], None]] = None

    def sort(self) -> None:
        self.items = sorted(self.items, key=lambda x: x.priority)
        if self.on_change:
            self.on_change()

    @abc.abstractmethod
    def add(self, name: str) -> None:
        ...

    @abc.abstractmethod
    def remove(self, item: Habit) -> None:
        ...


class Storage(abc.ABC):
    @abc.abstractmethod
    def get_user_habit_list(self, user: User) -> Optional[HabitList]:
        ...

    @abc.abstractmethod
    def save_user_habit_list(self, user: User, habit_list: HabitList):
        ...

    @abc.abstractmethod
    def get_or_create_user_habit_list(
        self, user: User, default_habit_list: HabitList
    ) -> HabitList:
        ...
