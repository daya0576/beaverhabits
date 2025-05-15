from datetime import datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel

from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.storage.storage import HabitList, HabitListBuilder, HabitStatus

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
    id = await views.create_user_habit(user, habit.name)
    return {"id": id, "name": habit.name}


@api_router.get("/habits/{habit_id}", tags=["habits"])
async def get_habit_detail(
    habit_id: str,
    user: User = Depends(current_active_user),
):
    habit = await views.get_user_habit(user, habit_id)
    return {
        "id": habit.id,
        "name": habit.name,
        "star": habit.star,
        "records": habit.records,
        "status": habit.status,
    }


class UpdateHabit(BaseModel):
    name: str | None = None
    star: bool | None = None
    status: HabitStatus | None = None


@api_router.put("/habits/{habit_id}", tags=["habits"])
async def put_habit(
    habit_id: str,
    habit: UpdateHabit,
    user: User = Depends(current_active_user),
):
    existingHabit = await views.get_user_habit(user, habit_id)
    if habit.name is not None:
        existingHabit.name = habit.name
    if habit.star is not None:
        existingHabit.star = habit.star
    if habit.status is not None:
        existingHabit.status = habit.status

    return {
        "id": existingHabit.id,
        "name": existingHabit.name,
        "star": existingHabit.star,
        "records": existingHabit.records,
        "status": existingHabit.status,
    }


@api_router.delete("/habits/{habit_id}", tags=["habits"])
async def delete_habit(
    habit_id: str,
    user: User = Depends(current_active_user),
):
    habit = await views.get_user_habit(user, habit_id)
    await views.remove_user_habit(user, habit)
    return {
        "id": habit.id,
        "name": habit.name,
        "star": habit.star,
        "records": habit.records,
        "status": habit.status,
    }
    

@api_router.get("/habits/{habit_id}/completions", tags=["habits"])
async def get_habit_completions(
    habit_id: str,
    date_fmt: str = "%d-%m-%Y",
    date_start: str | None = None,
    date_end: str | None = None,
    limit: int | None = 10,
    sort="asc",
    user: User = Depends(current_active_user),
):
    habit = await views.get_user_habit(user, habit_id)
    ticked_days = habit.ticked_days
    if not ticked_days:
        return []

    if date_start or date_end:
        if date_start and date_end:
            try:
                start = datetime.strptime(date_start, date_fmt.strip())
                end = datetime.strptime(date_end, date_fmt.strip())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")
            ticked_days = [x for x in ticked_days if start.date() <= x <= end.date()]
        else:
            raise HTTPException(
                status_code=400, detail="Both date_start and date_end are required"
            )

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
        day = datetime.strptime(tick.date, tick.date_fmt.strip()).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    habit = await views.get_user_habit(user, habit_id)
    await habit.tick(day, tick.done, tick.text)
    return {"day": day.strftime(tick.date_fmt), "done": tick.done}


def init_api_routes(app: FastAPI) -> None:
    app.include_router(api_router, prefix="/api/v1")
