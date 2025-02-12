import datetime
from dataclasses import dataclass, field

from beaverhabits.logging import logger
from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList, HabitStatus, List
from beaverhabits.utils import generate_short_hash

DAY_MASK = "%Y-%m-%d"
MONTH_MASK = "%Y/%m"


@dataclass(init=False)
class DictStorage:
    data: dict = field(default_factory=dict, metadata={"exclude": True})


@dataclass
class DictRecord(CheckedRecord, DictStorage):
    """
    # Read (d1~d3)
    persistent    ->     memory      ->     view
    d0: [x]              d0: [x]
                                            d1: [ ]
    d2: [x]              d2: [x]            d2: [x]
                                            d3: [ ]

    # Update:
    view(update)  ->     memory      ->     persistent
    d1: [ ]
    d2: [ ]              d2: [ ]            d2: [x]
    d3: [x]              d3: [x]            d3: [ ]
    """

    @property
    def day(self) -> datetime.date:
        date = datetime.datetime.strptime(self.data["day"], DAY_MASK)
        return date.date()

    @property
    def done(self) -> bool:
        return self.data.get("done", False)

    @done.setter
    def done(self, value: bool) -> None:
        self.data["done"] = value

    @property
    def text(self) -> str:
        return self.data.get("text", "")

    @text.setter
    def text(self, value: str) -> None:
        self.data["text"] = value


class HabitDataCache:
    def __init__(self, habit: "DictHabit"):
        self.habit = habit
        self.ticked_days = [r.day for r in self.habit.records if r.done]
        self.ticked_data = {r.day: r for r in self.habit.records}

    def refresh(self):
        self.ticked_days = [r.day for r in self.habit.records if r.done]
        self.ticked_data = {r.day: r for r in self.habit.records}


@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
    def __init__(self, data: dict) -> None:
        self.data = data
        self.cache = HabitDataCache(self)

    @property
    def list_id(self) -> str | None:
        return self.data.get("list_id")
    
    @list_id.setter
    def list_id(self, value: str | None) -> None:
        self.data["list_id"] = value

    @property
    def id(self) -> str:
        if "id" not in self.data:
            self.data["id"] = generate_short_hash(self.name)
        return self.data["id"]

    @id.setter
    def id(self, value: str) -> None:
        self.data["id"] = value

    @property
    def name(self) -> str:
        return self.data["name"]

    @name.setter
    def name(self, value: str) -> None:
        self.data["name"] = value

    @property
    def star(self) -> bool:
        return self.data.get("star", False)

    @star.setter
    def star(self, value: int) -> None:
        self.data["star"] = value

    @property
    def weekly_goal(self) -> int:
        return self.data.get("weekly_goal", 0)

    @weekly_goal.setter
    def weekly_goal(self, value: int) -> None:
        self.data["weekly_goal"] = value

    @property
    def status(self) -> HabitStatus:
        status_value = self.data.get("status")

        if status_value is None:
            return HabitStatus.ACTIVE

        try:
            return HabitStatus(status_value)
        except ValueError:
            logger.error(f"Invalid status value: {status_value}")
            self.data["status"] = None
            return HabitStatus.ACTIVE

    @status.setter
    def status(self, value: HabitStatus) -> None:
        self.data["status"] = value.value

    @property
    def records(self) -> list[DictRecord]:
        return [DictRecord(d) for d in self.data["records"]]

    @property
    def ticked_days(self) -> list[datetime.date]:
        return self.cache.ticked_days

    @property
    def ticked_data(self) -> dict[datetime.date, DictRecord]:
        return self.cache.ticked_data

    async def tick(
        self, day: datetime.date, done: bool, text: str | None = None
    ) -> CheckedRecord:
        # Find the record in the cache
        record = self.ticked_data.get(day)

        if record is not None:
            # Update only if necessary to avoid unnecessary writes
            new_data = {}
            if record.done != done:
                new_data["done"] = done
            if text is not None and record.text != text:
                new_data["text"] = text
            if new_data:
                record.data.update(new_data)

        else:
            # Update storage once
            data = {"day": day.strftime(DAY_MASK), "done": done}
            if text is not None:
                data["text"] = text
            self.data["records"].append(data)

        # Update the cache
        self.cache.refresh()

        return self.ticked_data[day]

    async def merge(self, other: "DictHabit") -> "DictHabit":
        self_ticks = {r.day for r in self.records if r.done}
        other_ticks = {r.day for r in other.records if r.done}
        result = sorted(list(self_ticks | other_ticks))

        d = {
            "name": self.name,
            "records": [
                {"day": day.strftime(DAY_MASK), "done": True} for day in result
            ],
        }
        return DictHabit(d)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DictHabit) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return f"[{self.id}]{self.name}<{self.status.value}>"

    __repr__ = __str__


@dataclass
class DictList(List[DictHabit], DictStorage):
    def __init__(self, data: dict) -> None:
        self.data = data
    
    @property
    def id(self) -> str:
        return self.data["id"]
    
    @property
    def name(self) -> str:
        return self.data["name"]
    
    @name.setter
    def name(self, value: str) -> None:
        self.data["name"] = value
    
    @property
    def habits(self) -> list[DictHabit]:
        return []  # Lists don't store habits directly, they're referenced by list_id in habits


@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    @property
    def habits(self) -> list[DictHabit]:
        return [DictHabit(d) for d in self.data["habits"]]

    @property
    def order(self) -> list[str]:
        return self.data.get("order", [])

    @order.setter
    def order(self, value: list[str]) -> None:
        self.data["order"] = value

    async def get_habit_by(self, habit_id: str) -> DictHabit | None:
        for habit in self.habits:
            if habit.id == habit_id:
                return habit

    async def add(self, name: str) -> None:
        d = {"name": name, "records": [], "id": generate_short_hash(name)}
        self.data["habits"].append(d)

    async def remove(self, item: DictHabit) -> None:
        self.data["habits"].remove(item.data)

    async def merge(self, other: "DictHabitList") -> "DictHabitList":
        result = set(self.habits).symmetric_difference(set(other.habits))

        # Merge the habit if it exists
        for self_habit in self.habits:
            for other_habit in other.habits:
                if self_habit == other_habit:
                    new_habit = await self_habit.merge(other_habit)
                    result.add(new_habit)

        return DictHabitList({"habits": [h.data for h in result]})
