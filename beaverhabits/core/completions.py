import datetime
from dataclasses import dataclass
from enum import Enum

from beaverhabits.logging import logger
from beaverhabits.storage.storage import Habit, HabitFrequency
from beaverhabits.utils import date_move, get_period_fist_day


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


def done(
    habit: Habit, days: list[datetime.date]
) -> dict[datetime.date, Completion] | None:
    cache = set(habit.ticked_days)
    result = {}
    for day in days:
        if day in cache:
            result[day] = Completion.done()
    return result


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
    habit: Habit, days: list[datetime.date]
) -> dict[datetime.date, Completion] | None:
    # Example:
    # - Ride mountain bike twice a week
    # - Visit my mother every second weekend
    p = habit.period
    if not p or not days:
        return None

    # Cache
    # days_min = date_move(min(days), -p.period_count, p.period_type)
    # days_max = date_move(max(days), p.period_count, p.period_type)
    # cache = [x for x in habit.ticked_days if days_min < x < days_max]
    # logger.debug(f"min: {days_min}, max: {days_max}, cache: {cache}")
    cache = habit.ticked_days
    logger.debug(f"Period: {p}")
    logger.debug(f"Cache: {cache}")

    # Iterate over the completion days
    result: set[datetime.date] = set()
    for start, end in PeriodIterator(cache, p):
        # Identify current period start point
        logger.debug(f"Start: {start}, End: {end}")
        done_days = sum(1 for d in cache if start <= d < end)
        if done_days >= p.target_count:
            # Mark them as completed
            result |= set(day for day in days if start <= day < end)

    return {day: Completion.period() for day in result}


COMPLETION_HANDLERS = [period, done]


def get_habit_date_completion(
    habit: Habit, days: list[datetime.date]
) -> dict[datetime.date, Completion]:
    result = {day: Completion.init() for day in days}
    for handler in COMPLETION_HANDLERS:
        completion = handler(habit, days)
        if completion:
            result = {**result, **completion}
    return result
