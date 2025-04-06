import datetime
from dataclasses import dataclass
from enum import Enum

from beaverhabits.logging import logger
from beaverhabits.storage.storage import EVERY_DAY, Habit, HabitFrequency
from beaverhabits.utils import date_move, get_period_fist_day, timeit


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


INIT, DONE, PERIOD_DONE = (Completion.init(), Completion.done(), Completion.period())


def done(
    habit: Habit, start: datetime.date, end: datetime.date
) -> dict[datetime.date, Completion] | None:
    return {day: DONE for day in habit.ticked_days if start <= day <= end}


class PeriodIterator:
    def __init__(self, days: list[datetime.date], period: HabitFrequency):
        self.i = 0
        self.days = days
        self.period = period

    def __iter__(self):
        return self

    def __next__(self):
        if self.i >= len(self.days):
            raise StopIteration

        start = get_period_fist_day(self.days[self.i], self.period.period_type)
        end = date_move(start, self.period.period_count, self.period.period_type)
        self.i += 1
        return start, end


def period(
    habit: Habit, start: datetime.date, end: datetime.date
) -> dict[datetime.date, Completion] | None:
    # Example:
    # - Ride mountain bike twice a week
    # - Visit my mother every second weekend
    p = habit.period
    if not p:
        return

    # Ignore default (everyday)
    if p == EVERY_DAY:
        return

    # Cache
    days_min = date_move(start, -p.period_count, p.period_type)
    days_max = date_move(end, p.period_count, p.period_type)
    cache = [x for x in habit.ticked_days if days_min <= x <= days_max]
    logger.debug(f"cache: {cache}, {days_min} <= day <= {days_max}")

    # Iterate over the completion days
    result: set[datetime.date] = set()
    for left, right in PeriodIterator(cache, p):
        # Identify current period start point
        logger.debug(f"Start: {start}, End: {end}")
        done_days = sum(1 for d in cache if start <= d < end)
        if done_days >= p.target_count:
            # Mark them as completed
            for i in range((right - left).days):
                result.add(left + datetime.timedelta(days=i))

    return {day: PERIOD_DONE for day in result}


COMPLETION_HANDLERS = [period, done]


@timeit
def get_habit_date_completion(
    habit: Habit, start: datetime.date, end: datetime.date
) -> dict[datetime.date, Completion]:
    result = {}
    for handler in COMPLETION_HANDLERS:
        completion = handler(habit, start, end)
        if completion:
            result = {**result, **completion}
    return result
