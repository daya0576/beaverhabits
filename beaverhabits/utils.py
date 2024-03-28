import datetime
import random
from typing import Callable, List, Optional

from beaverhabits.configs import settings
from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList


def dummy_days(days: int) -> List[datetime.date]:
    today = datetime.date.today()
    return [today - datetime.timedelta(days=i) for i in reversed(range(days))]


def dummy_records(days: int, pick: Optional[Callable] = None) -> List[CheckedRecord]:
    return [
        CheckedRecord(day=x, done=pick and pick() or False) for x in dummy_days(days)
    ]


def dummy_habit_list():
    items = []
    for name in ["Order pizz", "Running", "Table Tennis", "Clean", "Call mom"]:
        pick = lambda: random.randint(0, 3) == 0
        days = settings.INDEX_HABIT_ITEM_COUNT
        habit = Habit(name=name, records=dummy_records(days, pick=pick))
        items.append(habit)
    return HabitList(items=items)
