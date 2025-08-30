import datetime

from beaverhabits.logger import logger
from beaverhabits.storage.storage import EVERY_DAY, CheckedState, Habit, HabitFrequency
from beaverhabits.utils import date_move, get_period_fist_day, timeit


def done(
    habit: Habit, start: datetime.date, end: datetime.date
) -> dict[datetime.date, CheckedState] | None:
    return {
        day: record.state
        for day, record in habit.ticked_data.items()
        if start <= day <= end
        and record.state in (CheckedState.DONE, CheckedState.SKIPPED)
    }


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


@timeit(3)
def period(
    habit: Habit, start: datetime.date, end: datetime.date
) -> dict[datetime.date, CheckedState] | None:
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
        done_days = sum(1 for d in cache if left <= d < right)
        logger.debug(
            f"Start: {left}, End: {right}, done: {done_days}, target: {p.target_count}"
        )
        if done_days >= p.target_count:
            # Mark them as completed
            for i in range((right - left).days):
                result.add(left + datetime.timedelta(days=i))

    return {day: CheckedState.PERIOD_DONE for day in result}


COMPLETION_HANDLERS = [period, done]


def get_habit_date_completion(
    habit: Habit, start: datetime.date, end: datetime.date
) -> dict[datetime.date, CheckedState]:
    result = {}
    for handler in COMPLETION_HANDLERS:
        completions = handler(habit, start, end)
        if not completions:
            continue

        result = {**result, **completions}

    return result
