from typing import List
from fastapi import APIRouter, Depends, HTTPException

from beaverhabits.app.crud import (
    create_list,
    get_user_lists,
    update_list,
    create_habit,
)
from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user
from beaverhabits.app.schemas import (
    HabitListCreate,
    HabitListRead,
    HabitListUpdate,
    HabitCreate,
    HabitRead,
)

router = APIRouter(tags=["lists"])

@router.get("/lists", response_model=List[HabitListRead])
async def get_lists(
    user: User = Depends(current_active_user),
):
    """Get all lists for the current user."""
    return await get_user_lists(user)

@router.post("/lists", response_model=HabitListRead)
async def create_new_list(
    list_create: HabitListCreate,
    user: User = Depends(current_active_user),
):
    """Create a new list."""
    return await create_list(user, list_create.name, list_create.order)

@router.patch("/lists/{list_id}", response_model=HabitListRead)
async def update_list_details(
    list_id: int,
    list_update: HabitListUpdate,
    user: User = Depends(current_active_user),
):
    """Update list details."""
    updated_list = await update_list(
        list_id,
        user.id,
        name=list_update.name,
        order=list_update.order,
    )
    if not updated_list:
        raise HTTPException(status_code=404, detail="List not found")
    return updated_list

@router.post("/lists/{list_id}/habits", response_model=HabitRead)
async def create_list_habit(
    list_id: int,
    habit_create: HabitCreate,
    user: User = Depends(current_active_user),
):
    """Create a new habit in a list."""
    habit = await create_habit(
        user,
        list_id,
        habit_create.name,
        habit_create.order,
    )
    if not habit:
        raise HTTPException(status_code=404, detail="List not found")
    return habit
