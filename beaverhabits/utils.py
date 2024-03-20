import datetime
from typing import Callable, List, Optional

from .app.db import CheckedRecordModel


def dummy_days(days: int) -> List[datetime.date]:
    today = datetime.date.today()
    return [today - datetime.timedelta(days=i) for i in reversed(range(days))]


def dummy_records(
    days: int, pick: Optional[Callable] = None
) -> List[CheckedRecordModel]:
    return [
        CheckedRecordModel(day=x, done=pick and pick() or False)
        for x in dummy_days(days)
    ]
