from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from beaverhabits.app.auth import user_authenticate
from beaverhabits.app.crud import (
    get_user_habits,
    update_habit,
    toggle_habit_check,
    get_habit_checks,
)
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.app.schemas import (
    HabitRead,
    HabitUpdate,
    CheckedRecordRead,
)
from beaverhabits.logging import logger

router = APIRouter(tags=["habits"])

@router.get("/habits", response_model=List[HabitRead])
async def get_habits(
    list_id: int | None = None,
    user: User = Depends(current_active_user),
):
    """Get list of habits."""
    return await get_user_habits(user, list_id)

@router.get("/habits/{habit_id}", response_model=HabitRead)
async def get_habit_detail(
    habit_id: int,
    user: User = Depends(current_active_user),
):
    """Get detailed information about a specific habit."""
    habit = await update_habit(habit_id, user.id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit

@router.patch("/habits/{habit_id}", response_model=HabitRead)
async def update_habit_details(
    habit_id: int,
    habit_update: HabitUpdate,
    user: User = Depends(current_active_user),
):
    """Update habit details."""
    habit = await update_habit(
        habit_id,
        user.id,
        name=habit_update.name,
        order=habit_update.order,
        list_id=habit_update.list_id,
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit

@router.get("/habits/{habit_id}/completions", response_model=List[CheckedRecordRead])
async def get_habit_completions(
    habit_id: int,
    user: User = Depends(current_active_user),
):
    """Get completion records for a specific habit."""
    return await get_habit_checks(habit_id, user.id)

@router.post("/habits/{habit_id}/completions", response_model=CheckedRecordRead)
async def toggle_completion(
    habit_id: int,
    date: str,
    user: User = Depends(current_active_user),
):
    """Toggle completion status for a specific habit on a given date."""
    try:
        day = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    record = await toggle_habit_check(habit_id, user.id, day)
    if not record:
        raise HTTPException(status_code=404, detail="Habit not found")
    return record

@router.post("/habits/batch-completions")
async def batch_update_completions(
    habit_id: int,
    dates: List[str],
    user: User = Depends(current_active_user),
):
    """Update multiple completion statuses for a habit."""
    try:
        updated = []
        for date_str in dates:
            try:
                day = datetime.strptime(date_str, "%Y-%m-%d").date()
                record = await toggle_habit_check(habit_id, user.id, day)
                if record:
                    updated.append({
                        "date": date_str,
                        "done": record.done
                    })
            except ValueError:
                logger.error(f"Invalid date format for {date_str}")
                continue

        return {
            "habit_id": habit_id,
            "updated": updated
        }

    except Exception as e:
        logger.exception("Unexpected error in batch_update_completions")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        ) from e
