from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from beaverhabits import views
from beaverhabits.api.dependencies import current_habit_list
from beaverhabits.api.models import HabitListMeta, Tick, HabitCompletions
from beaverhabits.app.auth import user_authenticate
from beaverhabits.logging import logger
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.storage.storage import HabitList, HabitListBuilder, HabitStatus

router = APIRouter(tags=["habits"])


@router.get("/habits/meta")
async def get_habits_meta(
    habit_list: HabitList = Depends(current_habit_list),
):
    """Get habit list metadata."""
    return HabitListMeta(order=habit_list.order)


@router.put("/habits/meta")
async def put_habits_meta(
    meta: HabitListMeta,
    habit_list: HabitList = Depends(current_habit_list),
):
    """Update habit list metadata."""
    if meta.order is not None:
        habit_list.order = meta.order
    return {"order": habit_list.order}


@router.get("/habits")
async def get_habits(
    status: HabitStatus = HabitStatus.ACTIVE,
    habit_list: HabitList = Depends(current_habit_list),
):
    """Get list of habits."""
    habits = HabitListBuilder(habit_list).status(status).build()
    return [{"id": x.id, "name": x.name} for x in habits]


@router.get("/habits/{habit_id}")
async def get_habit_detail(
    habit_id: str,
    user: User = Depends(current_active_user),
):
    """Get detailed information about a specific habit."""
    habit = await views.get_user_habit(user, habit_id)
    return {
        "id": habit.id,
        "name": habit.name,
        "star": habit.star,
        "records": habit.records,
        "status": habit.status,
    }


@router.get("/habits/{habit_id}/completions")
async def get_habit_completions(
    habit_id: str,
    date_fmt: str = "%d-%m-%Y",
    date_start: str | None = None,
    date_end: str | None = None,
    limit: int | None = 10,
    sort="asc",
    user: User = Depends(current_active_user),
):
    """Get completion records for a specific habit."""
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


@router.post("/habits/{habit_id}/completions")
async def put_habit_completions(
    habit_id: str,
    tick: Tick,
    user: User = Depends(current_active_user),
):
    """Update completion status for a specific habit."""
    try:
        day = datetime.strptime(tick.date, tick.date_fmt.strip()).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    habit = await views.get_user_habit(user, habit_id)
    await habit.tick(day, tick.done)
    return {"day": day.strftime(tick.date_fmt), "done": tick.done}


@router.post("/habits/batch-completions")
async def batch_update_completions(data: HabitCompletions):
    """Update multiple completion statuses for a habit."""
    try:
        # Authenticate user
        user = await user_authenticate(data.email, data.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # Get the habit
        habit = await views.get_user_habit(user, data.habit_id)
        if not habit:
            raise HTTPException(
                status_code=404,
                detail=f"Habit with ID {data.habit_id} not found"
            )

        # Process each completion
        updated = []
        for completion in data.completions:
            try:
                # Parse date using the provided format
                day = datetime.strptime(completion.date, data.date_fmt).date()
                # Update the habit
                await habit.tick(day, completion.done)
                # Add to updated list
                updated.append({
                    "date": completion.date,
                    "done": completion.done
                })
            except ValueError as e:
                logger.error(f"Invalid date format for {completion.date}: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date format for {completion.date}"
                )
            except Exception as e:
                logger.error(f"Error updating habit for date {completion.date}: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update habit for date {completion.date}"
                )

        return {
            "habit_id": data.habit_id,
            "updated": updated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in batch_update_completions")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        ) from e
