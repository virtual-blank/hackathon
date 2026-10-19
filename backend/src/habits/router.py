import logging
import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from src.achievements.service import AchievementsService
from src.auth.deps import CurrentUserDep, CurrentUserIdDep, SessionDep
from src.habits.schemas import (
    HabitCreateSchema,
    HabitLogOutputSchema,
    HabitOutputSchema,
    HabitUpdateSchema,
    MarkedHabitOutputSchema,
)
from src.habits.service import HabitLogService, HabitsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/habits", tags=["🏃 Habits"])


# == CREATE HABIT ==
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=HabitOutputSchema,
    description="Create Habit",
)
async def create_habit(
    habit_data: HabitCreateSchema, user_id: CurrentUserIdDep, session: SessionDep, bt: BackgroundTasks
):
    service = HabitsService(session=session)
    try:
        new_habit = await service.create_habit(habit_data=habit_data, user_id=user_id)
        bt.add_task(AchievementsService.process_achievements_habits_bt, user_id=user_id)
        return new_habit
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        logger.exception("Не удалось создать привычку user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# == GET HABITS ==
@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[HabitOutputSchema],
    description="Get Habits",
)
async def get_habits(
    user_id: CurrentUserIdDep,
    session: SessionDep,
    target_user_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    habit_status: Literal["completed", "uncompleted"] | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    service = HabitsService(session=session)
    try:
        return await service.get_habits(
            user_id=user_id,
            target_user_id=target_user_id,
            start_date=start_date,
            end_date=end_date,
            status=habit_status,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Не удалось получить список привычек user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == GET HABIT LOGS ==
@router.get(
    "/logs",
    status_code=status.HTTP_200_OK,
    response_model=list[HabitLogOutputSchema],
    description="Get habit logs",
)
async def get_logs_in_range(
    user_id: CurrentUserIdDep,
    date_from: date,
    date_to: date,
    session: SessionDep,
    habit_id: uuid.UUID | None = None,
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    service = HabitLogService(session=session)
    try:
        return await service.get_logs_in_range(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            habit_id=habit_id,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Не удалось получить логи привычек user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == GET COMPLETED HABITS ==
@router.get(
    "/logs/completed",
    status_code=status.HTTP_200_OK,
    response_model=list[HabitOutputSchema],
    description="Get completed habits",
)
async def get_completed_habits(user_id: CurrentUserIdDep, target_date: date, session: SessionDep):
    service = HabitLogService(session=session)
    try:
        return await service.get_completed_habits_by_date(user_id=user_id, target_date=target_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Не удалось получить выполненные привычки user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == GET UNCOMPLETED HABITS ==
@router.get(
    "/logs/uncompleted",
    status_code=status.HTTP_200_OK,
    response_model=list[HabitOutputSchema],
    description="Get uncompleted habits",
)
async def get_uncompleted_habits(user_id: CurrentUserIdDep, target_date: date, session: SessionDep):
    service = HabitLogService(session=session)
    try:
        return await service.get_uncompleted_habits_by_date(user_id=user_id, target_date=target_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Не удалось получить невыполненные привычки user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == GET HABIT ==
@router.get(
    "/{habit_id}",
    status_code=status.HTTP_200_OK,
    response_model=HabitOutputSchema,
    description="Get Habit",
)
async def get_habit(user_id: CurrentUserIdDep, habit_id: uuid.UUID, session: SessionDep):
    service = HabitsService(session=session)
    try:
        habit = await service.get_habit(user_id=user_id, habit_id=habit_id)
        if habit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        return habit

    except HTTPException:
        raise
    except Exception:
        logger.exception("Не удалось получить привычку habit_id=%s user_id=%s", habit_id, user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == EDIT HABIT ==
@router.patch(
    "/{habit_id}",
    status_code=status.HTTP_200_OK,
    response_model=HabitOutputSchema,
    description="Update Habit",
)
async def update_habit(user_id: CurrentUserIdDep, habit_id: uuid.UUID, data: HabitUpdateSchema, session: SessionDep):
    service = HabitsService(session=session)
    try:
        habit = await service.update_habit(user_id=user_id, habit_id=habit_id, habit_data=data)
        if habit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        return habit

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Не удалось обновить привычку habit_id=%s user_id=%s", habit_id, user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == DELETE HABIT ==
@router.delete("/{habit_id}", status_code=status.HTTP_200_OK, description="Delete Habit")
async def delete_habit(user_id: CurrentUserIdDep, habit_id: uuid.UUID, session: SessionDep):
    service = HabitsService(session=session)
    try:
        deleted = await service.delete_habit(user_id=user_id, habit_id=habit_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        return {"detail": "Habit deleted"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        logger.exception("Не удалось удалить привычку habit_id=%s user_id=%s", habit_id, user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == COMPLETE OR UNCOMPLETE HABIT ==
@router.patch(
    "/{habit_id}/toggle",
    status_code=status.HTTP_200_OK,
    response_model=MarkedHabitOutputSchema,
    description="Click on habit (complete or uncomplete)",
)
async def mark_habit(current_user: CurrentUserDep, session: SessionDep, habit_id: uuid.UUID, bt: BackgroundTasks):
    service = HabitsService(session=session)
    try:
        updated_habit = await service.mark_habit(habit_id=habit_id, current_user=current_user)
        if updated_habit.is_completed:
            bt.add_task(
                AchievementsService.process_achievements_task_bt,
                user_id=current_user.id,
                streak_days=updated_habit.habit.current_streak_days,
            )
        return updated_habit
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.exception("Не удалось отметить привычку habit_id=%s user_id=%s", habit_id, current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
