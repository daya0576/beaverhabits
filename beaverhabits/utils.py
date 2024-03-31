import datetime
from typing import Callable, List, Optional, OrderedDict

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList


def dummy_days(days: int) -> List[datetime.date]:
    today = datetime.date.today()
    return [today - datetime.timedelta(days=i) for i in reversed(range(days))]


def dummy_records(days: int, pick: Optional[Callable] = None) -> List[CheckedRecord]:
    return [
        CheckedRecord(day=x, done=pick and pick() or False) for x in dummy_days(days)
    ]


def dummy_record_dict(limit: int) -> OrderedDict[datetime.date, CheckedRecord]:
    return OrderedDict((x, CheckedRecord(day=x, done=False)) for x in dummy_days(limit))
