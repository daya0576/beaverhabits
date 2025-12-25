import datetime
from typing import Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.core.completions import CStatus, get_habit_date_completion
from beaverhabits.storage.storage import (
    Habit,
    HabitFrequency,
    HabitList,
    HabitListBuilder,
    HabitStatus,
)

api_router = APIRouter()


async def current_habit_list(user: User = Depends(current_active_user)) -> HabitList:
    habit_list = await views.get_user_habit_list(user)
    if not habit_list:
        raise HTTPException(status_code=404, detail="No habits found")
    return habit_list


class HabitListMeta(BaseModel):
    order: list[str] | None = None


@api_router.get("/habits/meta", tags=["habits"])
async def get_habits_meta(
    habit_list: HabitList = Depends(current_habit_list),
):
    return HabitListMeta(order=habit_list.order)


@api_router.put("/habits/meta", tags=["habits"])
async def put_habits_meta(
    meta: HabitListMeta,
    habit_list: HabitList = Depends(current_habit_list),
):
    if meta.order is not None:
        habit_list.order = meta.order
    return {"order": habit_list.order}


@api_router.get("/habits", tags=["habits"])
async def get_habits(
    status: HabitStatus = HabitStatus.ACTIVE,
    habit_list: HabitList = Depends(current_habit_list),
):
    habits = HabitListBuilder(habit_list).status(status).build()
    return [{"id": x.id, "name": x.name} for x in habits]


class CreateHabit(BaseModel):
    name: str


@api_router.post("/habits", tags=["habits"])
async def post_habits(
    habit: CreateHabit,
    user: User = Depends(current_active_user),
):
    habit_list = await views.get_or_create_user_habit_list(
        user, views.dummy_empty_habit_list()
    )

    id = await habit_list.add(habit.name)
    logger.info(f"Created new habit {id} for user {user.email}")

    return {"id": id, "name": habit.name}


@api_router.get("/habits/{habit_id}", tags=["habits"])
async def get_habit_detail(
    habit_id: str,
    user: User = Depends(current_active_user),
):
    habit = await views.get_user_habit(user, habit_id)
    return format_json_response(habit)


class UpdateHabit(BaseModel):
    class UpdateHabitPeriod(BaseModel):
        period_type: Literal["D", "W", "M", "Y"]
        period_count: int
        target_count: int

    name: str | None = None
    star: bool | None = None
    status: HabitStatus | None = None
    period: UpdateHabitPeriod | None = None
    tags: list[str] | None = None


@api_router.put("/habits/{habit_id}", tags=["habits"])
async def put_habit(
    habit_id: str,
    habit: UpdateHabit,
    user: User = Depends(current_active_user),
):
    existing_habit = await views.get_user_habit(user, habit_id)
    if habit.name is not None:
        existing_habit.name = habit.name
    if habit.star is not None:
        existing_habit.star = habit.star
    if habit.status is not None:
        existing_habit.status = habit.status
    if habit.period is not None:
        existing_habit.period = HabitFrequency(
            target_count=habit.period.target_count,
            period_count=habit.period.period_count,
            period_type=habit.period.period_type,
        )
    if habit.tags is not None:
        existing_habit.tags = habit.tags

    return format_json_response(existing_habit)


@api_router.delete("/habits/{habit_id}", tags=["habits"])
async def delete_habit(
    habit_id: str,
    user: User = Depends(current_active_user),
):
    habit = await views.get_user_habit(user, habit_id)
    await views.remove_user_habit(user, habit)
    return format_json_response(habit)


@api_router.get("/habits/{habit_id}/completions", tags=["habits"])
async def get_habit_completions(
    habit_id: str,
    status: list[CStatus] | None = None,
    date_fmt: str = "%d-%m-%Y",
    date_start: str | None = None,
    date_end: str | None = None,
    limit: int | None = 10,
    sort="asc",
    user: User = Depends(current_active_user),
):

    if not (date_start or date_end):
        start, end = datetime.date.min, datetime.date.max
    elif date_start and date_end:
        try:
            start = datetime.datetime.strptime(date_start, date_fmt.strip()).date()
            end = datetime.datetime.strptime(date_end, date_fmt.strip()).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        raise HTTPException(
            status_code=400,
            detail="Both date_start and date_end must be provided",
        )

    if not status:
        status = [CStatus.DONE]

    habit = await views.get_user_habit(user, habit_id)
    status_map = get_habit_date_completion(habit, start, end)
    ticked_days = [
        day for day, stat in status_map.items() if any(s in stat for s in status)
    ]

    if sort not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="Invalid sort value")
    ticked_days = sorted(ticked_days, reverse=sort == "desc")

    if limit:
        ticked_days = ticked_days[:limit]

    return [x.strftime(date_fmt) for x in ticked_days]


class Tick(BaseModel):
    done: bool
    date: str
    text: str | None = None
    date_fmt: str = "%d-%m-%Y"


@api_router.post("/habits/{habit_id}/completions", tags=["habits"])
async def put_habit_completions(
    habit_id: str,
    tick: Tick,
    user: User = Depends(current_active_user),
):
    try:
        day = datetime.datetime.strptime(tick.date, tick.date_fmt.strip()).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    habit = await views.get_user_habit(user, habit_id)
    await habit.tick(day, tick.done, tick.text)
    return {"day": day.strftime(tick.date_fmt), "done": tick.done}


def format_json_response(habit: Habit) -> dict:
    return {
        "id": habit.id,
        "name": habit.name,
        "star": habit.star,
        "records": habit.records,
        "status": habit.status,
        "period": habit.period,
        "tags": habit.tags,
    }


def init_api_routes(app: FastAPI) -> None:
    app.include_router(api_router, prefix="/api/v1")
