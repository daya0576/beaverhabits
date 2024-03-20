from dataclasses import dataclass, field
from typing import Callable, List

from .app.db import HabitModel


@dataclass
class HabitList:
    on_change: Callable
    items: List[HabitModel] = field(default_factory=list)

    def add(self, item: HabitModel) -> None:
        self.items.append(item)
        self.on_change()

    def remove(self, item: HabitModel) -> None:
        self.items.remove(item)
        self.on_change()
