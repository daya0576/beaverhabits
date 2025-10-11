import datetime
from enum import Enum

from beaverhabits.logger import logger
from beaverhabits.storage.storage import (
    EVERY_DAY,
    CheckedRecord,
    Habit,
    HabitFrequency,
)
from beaverhabits.utils import date_move, get_period_fist_day, timeit


class CheckedState(Enum):
    UNKNOWN = "UNKNOWN"

    DONE = "DONE"
    SKIPPED = "SKIPPED"

    PERIOD_DONE = "PERIOD_DONE"


def get_checked_state(r: CheckedRecord) -> CheckedState:
    if r.skipped:
        return CheckedState.SKIPPED
    if r.done is True:
        return CheckedState.DONE
    return CheckedState.UNKNOWN


def done(
    habit: Habit, start: datetime.date, end: datetime.date
) -> dict[datetime.date, CheckedState] | None:
    return {day: CheckedState.DONE for day in habit.ticked_days if start <= day <= end}


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


def skipped(
    habit: Habit, start: datetime.date, end: datetime.date
) -> dict[datetime.date, CheckedState] | None:
    return {
        d: CheckedState.SKIPPED
        for d, r in habit.ticked_data.items()
        if start <= d <= end and r.skipped
    }


@timeit(3)
def period(
    habit: Habit, start: datetime.date, end: datetime.date
) -> dict[datetime.date, CheckedState] | None:
    # Example:
    # - Ride mountain bike twice a week
    # - Visit my mother every second weekend
    p = habit.period

    # Ignore default (everyday)
    if not p or p == EVERY_DAY:
        return

    # Cache
    days_min = date_move(start, -p.period_count, p.period_type)
    days_max = date_move(end, p.period_count, p.period_type)
    cache_ticked = sorted([x for x in habit.ticked_days if days_min <= x <= days_max])
    cache_skipped = {
        d: r
        for d, r in habit.ticked_data.items()
        if days_min <= d <= days_max and (r.skipped or r.done)
    }
    logger.debug(
        f"cache ({habit.name}): {days_min} <= day <= {days_max}, "
        f"ticked: {len(cache_ticked)}, skipped: {len(cache_skipped)}"
    )

    # Iterate over the completion days
    partial_days: set[datetime.date] = set()
    for left, right in PeriodIterator(sorted(cache_skipped.keys()), p):
        # Identify current period start point
        done_days = sum(1 for d in cache_ticked if left <= d < right)
        is_period_done = done_days >= p.target_count
        is_skipped = any(
            r.skipped for d, r in cache_skipped.items() if left <= d < right
        )
        logger.debug(
            f"Left: {left}, Right: {right}, "
            f"done: {done_days}, target: {p.target_count}, is_skipped: {is_skipped}"
        )
        if is_period_done or is_skipped:
            # Mark them as completed
            for i in range((right - left).days):
                partial_days.add(left + datetime.timedelta(days=i))

    result = {
        day: CheckedState.PERIOD_DONE for day in partial_days if start <= day <= end
    }
    logger.debug(f"Period result: {result}")
    return result


COMPLETION_HANDLERS = [period, skipped, done]


def get_habit_date_completion(
    habit: Habit, start: datetime.date, end: datetime.date
) -> dict[datetime.date, CheckedState]:
    result = {}
    for handler in COMPLETION_HANDLERS:
        completions = handler(habit, start, end)
        logger.debug(f"completions ({habit.name}): {result}")
        if not completions:
            continue

        result = {**result, **completions}

    logger.debug(f"result ({habit.name}): {result}")
    return result
