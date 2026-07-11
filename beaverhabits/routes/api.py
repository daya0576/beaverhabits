import datetime
import json
from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from loguru import logger
from pydantic import BaseModel

from beaverhabits import views
from beaverhabits.app.auth import user_from_token
from beaverhabits.app.crud import get_user_by_api_token
from beaverhabits.app.db import User
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.core.completions import CStatus, get_habit_date_completion
from beaverhabits.realtime import apply_tick, manager
from beaverhabits.storage.storage import (
    Habit,
    HabitFrequency,
    HabitList,
    HabitListBuilder,
    HabitListNotFoundError,
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


# ---------------------------------------------------------------------------
# Full-sync endpoints for native clients (whole-dict passthrough).
#
# export/import operate on the raw stored dict
# ({habits:[...], order, order_by, ...}) verbatim, so client-only fields
# (e.g. records[].updated_at, reminders) round-trip losslessly. This is
# distinct from the web import flow (which renames collisions and merges
# server-side); here the client has already merged and sends the final state.
#
# NOTE: defined before /habits/{habit_id} so "export"/"import" are not captured
# as a habit_id path param.
# ---------------------------------------------------------------------------


@api_router.get("/habits/export", tags=["habits"])
async def export_habit_list(user: User = Depends(current_active_user)):
    # Go through the storage layer (views.user_storage) so this works for both
    # USER_DISK and USER_DATABASE backends. A brand-new account has no list yet.
    try:
        habit_list = await views.user_storage.get_user_habit_list(user)
    except HabitListNotFoundError:
        return {"habits": []}
    return habit_list.data


class ImportHabitList(BaseModel):
    model_config = {"extra": "allow"}  # passthrough unknown top-level keys

    habits: list[dict]
    order: list[str] | None = None
    order_by: int | None = None


def _plain_copy(value):
    """Detach NiceGUI observable containers before building the merged result."""
    return json.loads(json.dumps(value))


def _merge_records(existing: list[dict], incoming: list[dict]) -> list[dict]:
    merged = _plain_copy(existing)
    by_day = {record.get("day"): record for record in merged if record.get("day")}
    for record in incoming:
        day = record.get("day")
        if day and day in by_day:
            by_day[day].update(record)
        else:
            new_record = _plain_copy(record)
            merged.append(new_record)
            if day:
                by_day[day] = new_record
    return merged


def _merge_habit_dict(existing: dict, incoming: dict) -> None:
    incoming_records = incoming.get("records")
    for key, value in incoming.items():
        if key != "records":
            existing[key] = _plain_copy(value)
    if incoming_records is not None:
        existing["records"] = _merge_records(
            existing.get("records", []), incoming_records
        )


def _merge_habit_lists(existing: dict, incoming: dict) -> dict:
    """Merge a native payload without deleting data omitted by the client."""
    merged = _plain_copy(existing)
    merged_habits = merged.setdefault("habits", [])
    by_id = {
        habit.get("id"): habit for habit in merged_habits if habit.get("id")
    }

    for habit in incoming.get("habits", []):
        habit_id = habit.get("id")
        if habit_id and habit_id in by_id:
            _merge_habit_dict(by_id[habit_id], habit)
        else:
            new_habit = _plain_copy(habit)
            merged_habits.append(new_habit)
            if habit_id:
                by_id[habit_id] = new_habit

    for key, value in incoming.items():
        if key not in {"habits", "order"}:
            merged[key] = _plain_copy(value)

    if "order" in incoming and incoming["order"] is not None:
        requested = incoming["order"]
        remaining = [
            habit_id
            for habit_id in merged.get("order", [])
            if habit_id not in requested
        ]
        unordered = [
            habit.get("id")
            for habit in merged_habits
            if habit.get("id") not in requested and habit.get("id") not in remaining
        ]
        merged["order"] = requested + remaining + unordered

    return merged


@api_router.post("/habits/import", tags=["habits"])
async def import_habit_list(
    payload: ImportHabitList,
    user: User = Depends(current_active_user),
):
    data = payload.model_dump(exclude_unset=True)
    data.setdefault("habits", [])

    # Only a genuinely missing list initializes storage. Existing data is merged
    # first so a stale, partial, or accidentally empty payload cannot erase it.
    try:
        habit_list = await views.user_storage.get_user_habit_list(user)
    except HabitListNotFoundError:
        merged = data
        await views.user_storage.init_user_habit_list(user, DictHabitList(merged))
    else:
        merged = _merge_habit_lists(habit_list.data, data)
        await views.user_storage.replace_user_habit_list(user, DictHabitList(merged))

    return {"ok": True, "count": len(merged["habits"])}


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
    status: str | None = None,
    date_fmt: str = "%d-%m-%Y",
    date_start: str | None = None,
    date_end: str | None = None,
    limit: int | None = 10,
    sort="asc",
    user: User = Depends(current_active_user),
):
    # Parse date range
    start, end = datetime.date.min, datetime.date.max
    if date_start:
        try:
            start = datetime.datetime.strptime(date_start, date_fmt.strip()).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    if date_end:
        try:
            end = datetime.datetime.strptime(date_end, date_fmt.strip()).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    if start > end:
        raise HTTPException(
            status_code=400, detail="date_start cannot be after date_end"
        )

    # Parse status filter
    cstatus_list = [CStatus.DONE]
    if status:
        cstatus_list = []
        for s in status.split(","):
            try:
                cstatus_list.append(CStatus[s.strip().upper()])
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {s}")

    habit = await views.get_user_habit(user, habit_id)
    status_map = get_habit_date_completion(habit, start, end)
    ticked_days = [
        day
        for day, stat in status_map.items()
        if any(s in stat for s in cstatus_list) and start <= day <= end
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
    await apply_tick(habit, day, tick.done, tick.text, user_id=str(user.id))
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


# ---------------------------------------------------------------------------
# Realtime tick over WebSocket.
#
# Each device opens one authenticated socket (?token=<jwt|api_token>). A tick
# is persisted (reusing habit.tick) and fanned out to the user's OTHER sockets,
# which apply it directly -- the payload is self-contained, so no follow-up
# pull is needed. Single worker (gunicorn -w 1) => in-process broadcast, no
# external broker required.
# ---------------------------------------------------------------------------


async def _authenticate_ws(token: str | None) -> User | None:
    if not token:
        return None
    if user := await user_from_token(token):
        return user
    if user := await get_user_by_api_token(token):
        return user
    return None


@api_router.websocket("/sync/ws")
async def sync_ws(websocket: WebSocket, token: str | None = Query(default=None)):
    user = await _authenticate_ws(token)
    if user is None:
        await websocket.close(code=1008)  # policy violation
        return

    user_id = str(user.id)
    await manager.connect(user_id, websocket)
    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("type") != "tick":
                continue

            # Persist the tick, reusing the existing storage path.
            try:
                day = datetime.datetime.strptime(msg["day"], "%Y-%m-%d").date()
                habit = await views.get_user_habit(user, msg["habit_id"])
                await apply_tick(
                    habit,
                    day,
                    bool(msg.get("done", False)),
                    msg.get("text"),
                    user_id=user_id,
                    exclude=websocket,
                )
            except Exception as e:
                logger.warning(f"[ws] failed to apply tick for {user.email}: {e}")
                continue

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)


def init_api_routes(app: FastAPI) -> None:
    app.include_router(api_router, prefix="/api/v1")
