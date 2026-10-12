import uuid
from fastapi import APIRouter, status, HTTPException

from src.auth.deps import SessionDep, CurrentUserIdDep
from src.habits.schemas import HabitOutputSchema, HabitCreateSchema, HabitUpdateSchema
from src.habits.service import HabitsService

router = APIRouter(prefix="/habits", tags=["🏃 Habits"])

# == CREATE HABIT ==
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=HabitOutputSchema, description="Create Habit")
async def create_habit(habit_data: HabitCreateSchema, user_id: CurrentUserIdDep, session: SessionDep):
    service = HabitsService(session=session)
    try:
        return await service.create_habit(habit_data=habit_data, user_id=user_id)
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
@router.patch("/{habit_id}", status_code=status.HTTP_200_OK, response_model=HabitOutputSchema, description="Update Habit")
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
