import contextlib
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from beaverhabits.logging import logger
from beaverhabits.sql.models import Habit, HabitList, CheckedRecord, User
from .db import get_async_session

get_async_session_context = contextlib.asynccontextmanager(get_async_session)

# List operations
async def create_list(user: User, name: str, order: int = 0) -> HabitList:
    async with get_async_session_context() as session:
        habit_list = HabitList(name=name, order=order, user_id=user.id)
        session.add(habit_list)
        await session.commit()
        await session.refresh(habit_list)
        logger.info(f"[CRUD] Created list {habit_list.id} for user {user.id}")
        return habit_list

async def get_user_lists(user: User) -> List[HabitList]:
    async with get_async_session_context() as session:
        stmt = select(HabitList).where(
            HabitList.user_id == user.id,
            HabitList.deleted == False
        ).order_by(HabitList.order)
        result = await session.execute(stmt)
        return list(result.scalars())

async def update_list(list_id: int, user_id: UUID, name: Optional[str] = None, 
                     order: Optional[int] = None, deleted: bool = False,
                     enable_letter_filter: Optional[bool] = None) -> Optional[HabitList]:
    async with get_async_session_context() as session:
        stmt = select(HabitList).where(HabitList.id == list_id, HabitList.user_id == user_id)
        result = await session.execute(stmt)
        habit_list = result.scalar_one_or_none()
        
        if habit_list:
            if name is not None:
                habit_list.name = name
            if order is not None:
                habit_list.order = order
            if enable_letter_filter is not None:
                habit_list.enable_letter_filter = enable_letter_filter
                await session.commit()
                await session.refresh(habit_list)
                logger.info(f"[CRUD] Updated list {list_id} letter filter to {enable_letter_filter}")
            elif deleted:
                # Mark list as deleted
                habit_list.deleted = True
                
                # Also mark all habits in this list as deleted
                stmt = select(Habit).where(
                    Habit.list_id == list_id,
                    Habit.user_id == user_id
                )
                result = await session.execute(stmt)
                habits = result.scalars()
                for habit in habits:
                    habit.deleted = True
                
                await session.commit()
                await session.refresh(habit_list)
                logger.info(f"[CRUD] Marked list {list_id} and its habits as deleted")
            else:
                await session.commit()
                await session.refresh(habit_list)
                logger.info(f"[CRUD] Updated list {list_id}")
            
        return habit_list

# Habit operations
async def create_habit(user: User, name: str, list_id: Optional[int] = None, order: int = 0) -> Optional[Habit]:
    async with get_async_session_context() as session:
        if list_id is not None:
            # Verify list belongs to user
            stmt = select(HabitList).where(
                HabitList.id == list_id, 
                HabitList.user_id == user.id,
                HabitList.deleted == False
            )
            result = await session.execute(stmt)
            habit_list = result.scalar_one_or_none()
            
            if not habit_list:
                logger.warning(f"[CRUD] List {list_id} not found for user {user.id}")
                return None
            
        habit = Habit(name=name, order=order, list_id=list_id, user_id=user.id)
        session.add(habit)
        await session.commit()
        await session.refresh(habit)
        logger.info(f"[CRUD] Created habit {habit.id} in list {list_id}")
        return habit

async def get_user_habits(user: User, list_id: Optional[int] = None) -> List[Habit]:
    async with get_async_session_context() as session:
        stmt = select(Habit).where(
            Habit.user_id == user.id,
            Habit.deleted == False
        )
        if list_id:
            stmt = stmt.join(HabitList).where(
                Habit.list_id == list_id,
                HabitList.deleted == False
            )
        stmt = stmt.order_by(Habit.order)
        result = await session.execute(stmt)
        return list(result.scalars())

async def update_habit(habit_id: int, user_id: UUID, name: Optional[str] = None, 
                      order: Optional[int] = None, list_id: Optional[int] = None,
                      weekly_goal: Optional[int] = None, deleted: bool = False,
                      star: Optional[bool] = None) -> Optional[Habit]:
    async with get_async_session_context() as session:
        stmt = select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
        result = await session.execute(stmt)
        habit = result.scalar_one_or_none()
        
        if habit:
            if name is not None:
                habit.name = name
            if order is not None:
                habit.order = order
            if list_id is not None:
                # Verify new list belongs to user and is not deleted
                list_stmt = select(HabitList).where(
                    HabitList.id == list_id, 
                    HabitList.user_id == user_id,
                    HabitList.deleted == False
                )
                list_result = await session.execute(list_stmt)
                if list_result.scalar_one_or_none():
                    habit.list_id = list_id
            if weekly_goal is not None:
                habit.weekly_goal = weekly_goal
            if star is not None:
                habit.star = star
            if deleted:
                habit.deleted = True
            await session.commit()
            await session.refresh(habit)
            logger.info(f"[CRUD] {'Marked habit as deleted' if deleted else 'Updated habit'} {habit_id}")
            
        return habit

# Checked records operations
async def toggle_habit_check(habit_id: int, user_id: UUID, day: date, text: str | None = None, value: bool | None = None) -> Optional[CheckedRecord]:
    async with get_async_session_context() as session:
        # Verify habit belongs to user and list is not deleted
        habit_stmt = select(Habit).join(HabitList).where(
            Habit.id == habit_id,
            Habit.user_id == user_id,
            HabitList.deleted == False
        )
        habit_result = await session.execute(habit_stmt)
        habit = habit_result.scalar_one_or_none()
        
        if not habit:
            logger.warning(f"[CRUD] Habit {habit_id} not found for user {user_id}")
            return None
            
        # Find existing record
        stmt = select(CheckedRecord).where(
            CheckedRecord.habit_id == habit_id,
            CheckedRecord.day == day
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if value is None:  # Not set - delete record if exists
            if record:
                await session.delete(record)
                await session.commit()
                logger.info(f"[CRUD] Deleted habit {habit_id} check for {day}")
                return None
        else:  # Checked or Skipped
            if record:
                # Update existing record
                record.done = value
                if text is not None:  # Update text only if provided
                    record.text = text
            else:
                # Create new record
                record = CheckedRecord(habit_id=habit_id, day=day, done=value, text=text)
                session.add(record)
            
            await session.commit()
            await session.refresh(record)
            logger.info(f"[CRUD] Set habit {habit_id} check for {day} to {value}")
            return record

async def get_habit_checks(habit_id: int, user_id: UUID) -> List[CheckedRecord]:
    async with get_async_session_context() as session:
        # Verify habit belongs to user and list is not deleted
        habit_stmt = select(Habit).join(HabitList).where(
            Habit.id == habit_id,
            Habit.user_id == user_id,
            HabitList.deleted == False
        )
        habit_result = await session.execute(habit_stmt)
        if not habit_result.scalar_one_or_none():
            logger.warning(f"[CRUD] Habit {habit_id} not found for user {user_id}")
            return []
            
        stmt = select(CheckedRecord).where(CheckedRecord.habit_id == habit_id)
        result = await session.execute(stmt)
        return list(result.scalars())

async def get_user_count() -> int:
    async with get_async_session_context() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        user_count = len(result.all())
        return user_count
