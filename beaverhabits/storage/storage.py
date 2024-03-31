import abc
from dataclasses import dataclass, field
import datetime
from typing import Callable, List, Optional, OrderedDict


from beaverhabits.app.db import User


@dataclass
class CheckedRecord:
    day: datetime.date
    done: bool

    def __str__(self):
        return f"{self.day} {'[x]' if self.done else '[ ]'}"

    __repr__ = __str__


@dataclass
class Habit:
    name: str
    records: list[CheckedRecord] = field(default_factory=list)

    def get_records_by_date(
        self, days: List[datetime.date]
    ) -> OrderedDict[datetime.date, CheckedRecord]:
        all_records_by_date = OrderedDict(
            (x, CheckedRecord(day=x, done=False)) for x in days
        )
        for x in self.records:
            all_records_by_date[x.day] = x
        return all_records_by_date

    def tick(self, record: CheckedRecord) -> None:
        ...

    def __str__(self):
        return self.name

    __repr__ = __str__


@dataclass
class HabitList:
    items: List[Habit] = field(default_factory=list)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    on_change: Optional[Callable[[], None]] = None

    def add(self, name: str) -> None:
        self.items.append(Habit(name=name))
        if self.on_change:
            self.on_change()

    def remove(self, item: Habit) -> None:
        self.items.remove(item)
        if self.on_change:
            self.on_change()


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
