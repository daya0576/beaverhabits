import datetime
from dataclasses import dataclass
from enum import Enum

from beaverhabits.storage.storage import Habit


@dataclass
class Completion:
    Status = Enum("CStatus", [("INIT", 1), ("DONE", 2), ("PERIOD_DONE", 3)])

    status: "Status"

    @classmethod
    def init(cls):
        return cls(cls.Status.INIT)

    @classmethod
    def done(cls):
        return cls(cls.Status.DONE)

    @classmethod
    def period(cls):
        return cls(cls.Status.PERIOD_DONE)


def done(habit: Habit, day: datetime.date) -> Completion | None:
    if day in habit.ticked_days:
        return Completion.done()


def periodic(habit: Habit, day: datetime.date) -> Completion | None:
    # Examples:
    # Ride mountain bike twice a week
    # Visit my mother every second weekend
    period = habit.period
    if not period:
        return None

    # Search backward & forward
    start, end = day - period.interval_timedelta, day + period.interval_timedelta
    if habit.ticked_count(start, end) >= period.freq:
        return Completion.period()


COMPLETION_HANDLERS = [done, periodic]


def get_habit_date_completion(habit: Habit, day: datetime.date) -> Completion:
    for handler in COMPLETION_HANDLERS:
        completion = handler(habit, day)
        if completion:
            return completion

    return Completion.init()
