import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from src.achievements.service import AchievementsService
from src.auth.deps import CurrentUserDep, CurrentUserIdDep, SessionDep
from src.habits.schemas import HabitCreateSchema, HabitOutputSchema, HabitUpdateSchema, MarkedHabitOutputSchema
from src.habits.service import HabitsService

router = APIRouter(prefix="/habits", tags=["🏃 Habits"])


# == CREATE HABIT ==
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=HabitOutputSchema, description="Create Habit")
async def create_habit(
    habit_data: HabitCreateSchema, user_id: CurrentUserIdDep, session: SessionDep, bt: BackgroundTasks
):
    service = HabitsService(session=session)
    try:
        new_habit = await service.create_habit(habit_data=habit_data, user_id=user_id)
        ach_service = AchievementsService(session=session)
        bt.add_task(ach_service.check_total_habits_count_achievements, user_id=user_id)
        return new_habit
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


# == GET HABIT ==
@router.get("/{habit_id}", status_code=status.HTTP_200_OK, response_model=HabitOutputSchema, description="Get Habit")
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == GET HABITS ==
@router.get("/", status_code=status.HTTP_200_OK, response_model=list[HabitOutputSchema], description="Get Habits")
async def get_habits(user_id: CurrentUserIdDep, session: SessionDep):
    service = HabitsService(session=session)
    try:
        return await service.get_habits(user_id=user_id)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == EDIT HABIT ==
@router.patch(
    "/{habit_id}", status_code=status.HTTP_200_OK, response_model=HabitOutputSchema, description="Update Habit"
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
        ach_service = AchievementsService(session=session)
        bt.add_task(
            ach_service.check_streak_achievements,
            user_id=current_user.id,
            streak_days=updated_habit.habit.current_streak_days,
        )
        return updated_habit
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
