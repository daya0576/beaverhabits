from dataclasses import dataclass, field
import datetime
from typing import List

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList


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
        date = datetime.datetime.strptime(self.data["day"], "%Y-%m-%d")
        return date.date()

    @property
    def done(self) -> bool:
        return self.data["done"]

    @done.setter
    def done(self, value: bool) -> None:
        self.data["done"] = value


@dataclass
class DictHabit(Habit[DictRecord], DictStorage):
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
    def records(self) -> list[DictRecord]:
        return [DictRecord(d) for d in self.data["records"]]

    def get_records_by_days(self, days: List[datetime.date]) -> List[DictRecord]:
        d_r = {r.day: r for r in self.records}

        records = []
        for day in days:
            persistent_record = d_r.get(day)
            if persistent_record:
                records.append(persistent_record)
            else:
                records.append(
                    DictRecord({"day": day.strftime("%Y-%m-%d"), "done": False})
                )
        return records

    async def tick(self, record: DictRecord) -> None:
        if record.day not in {r.day for r in self.records}:
            self.data["records"].append(record.data)


@dataclass
class DictHabitList(HabitList[DictHabit], DictStorage):
    @property
    def habits(self) -> list[DictHabit]:
        self.sort()
        return [DictHabit(d) for d in self.data["habits"]]

    async def add(self, name: str) -> None:
        self.data["habits"].append({"name": name, "records": []})

    async def remove(self, item: DictHabit) -> None:
        self.data["habits"].remove(item.data)

    def sort(self) -> None:
        self.data["habits"].sort(key=lambda x: x.get("star", False), reverse=True)

    def __len__(self) -> int:
        return len(self.habits)
