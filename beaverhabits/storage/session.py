from dataclasses import dataclass, field
import datetime
from typing import List, Optional
import nicegui

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList, SessionStorage

KEY_NAME = "user_habit_list"


@dataclass(init=False)
class DictStorage:
    data: dict = field(default_factory=dict, metadata={"exclude": True})

    def on_update(self, **kwargs):
        self.data.update(kwargs)

    def on_insert(self, key, item):
        items = self.data[key]
        if item not in items:
            items.append(item)

    @staticmethod
    def dict_factory(x):
        exclude_fields = ("data",)
        return {k: v for (k, v) in x if k not in exclude_fields}


@dataclass
class SessionRecord(CheckedRecord, DictStorage):
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
class SessionHabit(Habit[SessionRecord], DictStorage):
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
    def records(self) -> list[SessionRecord]:
        return [SessionRecord(d) for d in self.data["records"]]

    def get_records_by_days(self, days: List[datetime.date]) -> List[SessionRecord]:
        d_r = {r.day: r for r in self.records}

        records = []
        for day in days:
            persistent_record = d_r.get(day)
            if persistent_record:
                records.append(persistent_record)
            else:
                records.append(
                    SessionRecord({"day": day.strftime("%Y-%m-%d"), "done": False})
                )
        return records

    async def tick(self, record: SessionRecord) -> None:
        if record.day not in {r.day for r in self.records}:
            self.data["records"].append(record.data)


@dataclass
class SessionHabitList(HabitList[SessionHabit], DictStorage):
    @property
    def habits(self) -> list[SessionHabit]:
        self.sort()
        return [SessionHabit(d) for d in self.data["habits"]]

    async def add(self, name: str) -> None:
        self.data["habits"].append({"name": name, "records": []})

    async def remove(self, item: SessionHabit) -> None:
        self.data["habits"].remove(item.data)

    def sort(self) -> None:
        self.data["habits"].sort(key=lambda x: x.get("star", False), reverse=True)


class NiceGUISessionStorage(SessionStorage[SessionHabitList]):
    def get_user_habit_list(self) -> Optional[SessionHabitList]:
        d = nicegui.app.storage.user.get(KEY_NAME)
        if not d:
            return None
        return SessionHabitList(d)

    def save_user_habit_list(self, habit_list: SessionHabitList) -> None:
        nicegui.app.storage.user[KEY_NAME] = habit_list.data
