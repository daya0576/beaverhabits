import datetime
from copy import deepcopy
from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from loguru import logger
from pydantic import BaseModel

from beaverhabits import views
from beaverhabits.app import crud
from beaverhabits.app.auth import user_from_token
from beaverhabits.app.crud import get_user_by_api_token
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.core.completions import CStatus, get_habit_date_completion
from beaverhabits.events import HabitListChanged, publish
from beaverhabits.realtime import manager
from beaverhabits.storage.storage import (
    Habit,
    HabitFrequency,
    HabitList,
    HabitListBuilder,
    HabitListNotFoundError,
    HabitStatus,
    habits_in_group_order,
)

api_router = APIRouter()


@api_router.delete("/account", status_code=204, tags=["account"])
async def delete_account(user: User = Depends(current_active_user)) -> Response:
    """Remove personal data and archive an anonymous disabled account record."""
    await views.delete_user_account(user)
    return Response(status_code=204)


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
# Full-sync endpoints for native clients.
#
# Export preserves the raw records but arranges habits in the same grouped
# order as the web homepage. Import remains a whole-dict passthrough. This is
# distinct from the web import flow (which renames collisions and merges
# server-side); here the client has already merged and sends the final state.
#
# NOTE: defined before /habits/{habit_id} so "export"/"import" are not captured
# as a habit_id path param.
# ---------------------------------------------------------------------------


def _habit_list_export_data(habit_list: HabitList) -> dict:
    snapshot = deepcopy(habit_list.data)
    active_habits = HabitListBuilder(habit_list).status(HabitStatus.ACTIVE).build()
    grouped_active = habits_in_group_order(active_habits)
    all_habits = HabitListBuilder(habit_list).build()

    ordered_ids = [str(habit.id) for habit in grouped_active]
    seen = set(ordered_ids)
    for habit in all_habits:
        habit_id = str(habit.id)
        if habit_id not in seen:
            ordered_ids.append(habit_id)
            seen.add(habit_id)

    raw_habits = snapshot.get("habits", [])
    by_id = {str(habit["id"]): habit for habit in raw_habits if "id" in habit}
    for habit in raw_habits:
        habit_id = str(habit.get("id"))
        if habit_id not in seen:
            ordered_ids.append(habit_id)
            seen.add(habit_id)

    snapshot["habits"] = [
        by_id[habit_id] for habit_id in ordered_ids if habit_id in by_id
    ]
    snapshot["order"] = ordered_ids
    return snapshot


@api_router.get("/habits/export", tags=["habits"])
async def export_habit_list(user: User = Depends(current_active_user)):
    try:
        habit_list = await views.user_storage.get_user_habit_list(user)
    except HabitListNotFoundError:
        return {"habits": []}
    return _habit_list_export_data(habit_list)


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
    text = "" if "text" in tick.model_fields_set and tick.text is None else tick.text
    await habit.tick(day, tick.done, text)
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


def _websocket_tick_text(message: dict) -> str | None:
    text = message.get("text")
    return "" if "text" in message and text is None else text


async def _authenticate_ws(token: str | None) -> User | None:
    if not token:
        return None
    if user := await user_from_token(token):
        return user
    if user := await get_user_by_api_token(token):
        return user
    return None


async def _apply_push_habit_list(user: User, msg: dict) -> None:
    """Merge incoming habit metadata into the stored list, preserving all records."""
    habit_list = await views.get_user_habit_list(user)
    if habit_list is None:
        return

    incoming_habits: list[dict] = msg.get("habits", [])
    incoming_by_id = {h["id"]: h for h in incoming_habits if "id" in h}

    # Update metadata for existing habits; add new ones.
    existing_ids = {str(h.id) for h in habit_list.habits}
    for h in habit_list.habits:
        if (incoming := incoming_by_id.get(str(h.id))) is None:
            continue
        if "name" in incoming:
            h.name = incoming["name"]
        if "star" in incoming:
            h.star = incoming["star"]
        if "status" in incoming:
            from beaverhabits.storage.storage import HabitStatus as _HS

            try:
                h.status = _HS(incoming["status"])
            except ValueError:
                pass
        if "period" in incoming:
            from beaverhabits.storage.storage import HabitFrequency as _HF

            p = incoming["period"]
            h.period = _HF.from_dict(p) if p else None
        if "tags" in incoming:
            h.tags = incoming["tags"]
        if "reminders" in incoming:
            h.data["reminders"] = incoming["reminders"]

    for habit_id, incoming in incoming_by_id.items():
        if habit_id not in existing_ids:
            await habit_list.add(incoming.get("name", ""), tags=incoming.get("tags"))
            # Set id to client-generated value.
            for h in habit_list.habits:
                if h.name == incoming.get("name") and str(h.id) != habit_id:
                    h.id = habit_id
                    break

    if "order" in msg:
        habit_list.order = msg["order"]
    if "order_by" in msg:
        from beaverhabits.storage.storage import HabitOrder as _HO

        try:
            habit_list.order_by = _HO(msg["order_by"])
        except ValueError, KeyError:
            pass


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
            msg_type = msg.get("type")

            if msg_type == "push_tick":
                logger.info(
                    f"[ws] received push_tick user={user_id} "
                    f"request={msg.get('request_id')} habit={msg.get('habit_id')} "
                    f"day={msg.get('day')}"
                )
                try:
                    day = datetime.datetime.strptime(msg["day"], "%Y-%m-%d").date()
                    habit = await views.get_user_habit(user, msg["habit_id"])
                    text = _websocket_tick_text(msg)
                    record = await habit.tick(day, bool(msg.get("done", False)), text)
                    await websocket.send_json(
                        {
                            "type": "tick_ack",
                            "request_id": msg["request_id"],
                            "timestamp": record.timestamp,
                        }
                    )
                except Exception as e:
                    logger.warning(f"[ws] failed to tick habit for {user.email}: {e}")

            elif msg_type == "push_habit_list":
                logger.info(
                    f"[ws] received push_habit_list user={user_id} "
                    f"request={msg.get('request_id')} "
                    f"habits={len(msg.get('habits', []))}"
                )
                try:
                    await _apply_push_habit_list(user, msg)
                    timestamp = int(
                        datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000
                    )
                    await websocket.send_json(
                        {
                            "type": "habit_list_ack",
                            "request_id": msg["request_id"],
                            "timestamp": timestamp,
                        }
                    )
                    payload = {
                        k: v for k, v in msg.items() if k not in ("type", "request_id")
                    }
                    publish(HabitListChanged(user_id=user_id, payload=payload))
                except Exception as e:
                    logger.warning(
                        f"[ws] failed to apply habit list for {user.email}: {e}"
                    )

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)


def init_api_routes(app: FastAPI) -> None:
    app.include_router(api_router, prefix="/api/v1")
