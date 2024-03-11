import datetime
from dataclasses import dataclass, field
from typing import Callable, List


@dataclass
class Record:
    day: datetime.date


@dataclass
class CheckedRecord(Record):
    done: bool = False


@dataclass
class Habit:
    name: str
    items: List[CheckedRecord] = field(default_factory=list)


@dataclass
class HabitList:
    title: str
    on_change: Callable
    items: List[Habit] = field(default_factory=list)

    def add(self, item: Habit) -> None:
        self.items.append(item)
        self.on_change()

    def remove(self, item: Habit) -> None:
        self.items.remove(item)
        self.on_change()
