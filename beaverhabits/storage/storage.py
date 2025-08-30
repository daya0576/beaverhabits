import datetime
import re
from dataclasses import asdict, dataclass
from enum import Enum, auto
from typing import List, Literal, Optional, Protocol, Self

from dataclasses_json import DataClassJsonMixin

from beaverhabits.app.db import User
from beaverhabits.utils import PERIOD_TYPES, D


class CheckedState(Enum):
    UNKNOWN = "UNKNOWN"
    DONE = "DONE"
    SKIPPED = "SKIPPED"


class CheckedRecord(Protocol):
    @property
    def day(self) -> datetime.date: ...

    @property
    def done(self) -> bool: ...

    @done.setter
    def done(self, value: bool) -> None: ...

    @property
    def text(self) -> str: ...

    @text.setter
    def text(self, value: str) -> None: ...

    @property
    def state(self) -> CheckedState: ...

    @state.setter
    def state(self, value: CheckedState) -> None: ...

    def __str__(self):
        return f"{self.day} {'[x]' if self.done else '[ ]'}"

    __repr__ = __str__


class HabitStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archive"
    SOLF_DELETED = "soft_delete"

    @classmethod
    def all(cls) -> tuple:
        return tuple(cls.__members__.values())


@dataclass
class HabitFrequency:
    PATTERN = re.compile(r"(\d+)\/(\d+)([DWMY])")

    # Moving window
    period_type: Literal["D", "W", "M", "Y"]
    period_count: int

    # Target frequency
    target_count: int

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            period_type=data["period_type"],
            period_count=data["period_count"],
            target_count=data["target_count"],
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def to_str(self) -> str:
        return f"{self.target_count}/{self.period_count}{self.period_type}"

    @classmethod
    def from_str(cls, value: str) -> Self:
        # Parse from pattern
        m = re.match(cls.PATTERN, value)

        # Extract the values
        if not m:
            raise ValueError(f"Invalid pattern: {value}")

        t_c, p_c, p_t = m.groups()[1:]
        if p_t not in PERIOD_TYPES:
            raise ValueError(f"Invalid period type: {p_t}")
        if not p_c.isdigit() or not t_c.isdigit():
            raise ValueError(f"Invalid period count: {p_c} or target count: {t_c}")
        t_c, p_c = int(t_c), int(p_c)

        # Create the object
        return cls(p_t, p_c, t_c)

    def __eq__(self, other):
        if isinstance(other, HabitFrequency):
            return (
                self.period_type == other.period_type
                and self.period_count == other.period_count
                and self.target_count == other.target_count
            )
        return False


EVERY_DAY = HabitFrequency(D, 1, 1)


class Habit[R: CheckedRecord](Protocol):
    @property
    def habit_list(self) -> "HabitList": ...

    @property
    def id(self) -> str | int: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, value: str) -> None: ...

    @property
    def tags(self) -> list[str]: ...

    @tags.setter
    def tags(self, value: list[str]) -> None: ...

    @property
    def star(self) -> bool: ...

    @star.setter
    def star(self, value: int) -> None: ...

    @property
    def records(self) -> list[R]: ...

    @property
    def status(self) -> HabitStatus: ...

    @status.setter
    def status(self, value: HabitStatus) -> None: ...

    @property
    def period(self) -> HabitFrequency | None: ...

    @period.setter
    def period(self, value: HabitFrequency | None) -> None: ...

    @property
    def ticked_days(self) -> list[datetime.date]: ...

    def ticked_count(
        self, start: datetime.date | None = None, end: datetime.date | None = None
    ) -> int: ...

    @property
    def ticked_data(self) -> dict[datetime.date, R]: ...

    def record_by(self, day: datetime.date) -> Optional[R]:
        return self.ticked_data.get(day)

    async def tick(
        self, day: datetime.date, done: bool, text: str | None = None
    ) -> CheckedRecord: ...

    def copy(self) -> "Habit": ...

    def to_dict(self) -> dict: ...

    def __str__(self):
        return self.name

    __repr__ = __str__


class HabitOrder(Enum):
    NAME = auto()
    CATEGORY = auto()
    MANUALLY = auto()


@dataclass
class Backup(DataClassJsonMixin):
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None


class HabitList[H: Habit](Protocol):

    @property
    def habits(self) -> List[H]: ...

    @property
    def order(self) -> List[str]: ...

    @order.setter
    def order(self, value: List[str]) -> None: ...

    @property
    def order_by(self) -> HabitOrder: ...

    @order_by.setter
    def order_by(self, value: HabitOrder) -> None: ...

    @property
    def backup(self) -> Backup: ...

    @backup.setter
    def backup(self, value: Backup) -> None: ...

    async def add(self, name: str, tags: list | None = None) -> str: ...

    async def remove(self, item: H) -> None: ...

    async def get_habit_by(self, habit_id: str) -> Optional[H]: ...


class SessionStorage[L: HabitList](Protocol):
    def get_user_habit_list(self) -> Optional[L]: ...

    def save_user_habit_list(self, habit_list: L) -> None: ...


class UserStorage[L: HabitList](Protocol):
    async def get_user_habit_list(self, user: User) -> L: ...

    async def init_user_habit_list(self, user: User, habit_list: L) -> None: ...


class HabitListBuilder:
    def __init__(self, habit_list: HabitList):
        self.habit_list = habit_list
        self.status_list = (
            HabitStatus.ACTIVE,
            HabitStatus.ARCHIVED,
        )
        self.order_by = HabitOrder.MANUALLY

    def status(self, *status: HabitStatus) -> Self:
        self.status_list = status
        return self

    def build(self) -> List[Habit]:
        # Deep copy the list
        habits = [x for x in self.habit_list.habits if x.status in self.status_list]

        # sort by order
        if self.habit_list.order_by == HabitOrder.NAME:
            habits.sort(key=lambda x: x.name.lower())
        elif self.habit_list.order_by == HabitOrder.CATEGORY:
            habits.sort(key=lambda x: (0, x.tags[0].lower()) if x.tags else (1, ""))
        elif o := self.habit_list.order:
            habits.sort(
                key=lambda x: (o.index(str(x.id)) if str(x.id) in o else float("inf"))
            )

        # sort by star
        habits.sort(key=lambda x: x.star, reverse=True)

        # Sort by status
        all_status = HabitStatus.all()
        habits.sort(key=lambda x: all_status.index(x.status))

        return habits


@dataclass
class ImageObject(DataClassJsonMixin):
    id: str
    url: str
    blob: bytes | None = None
    owner: str | None = None


class ImageStorage(Protocol):
    async def save(self, byte_data: bytes, user: User | None = None) -> ImageObject: ...

    async def get(self, uuid: str, user: User | None = None) -> ImageObject | None: ...
