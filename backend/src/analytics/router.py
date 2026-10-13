import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from src.auth.deps import CurrentUserIdDep
from src.analytics.schemas import DashboardResponseSchema, HeatmapResponseSchema
from src.analytics.service import AnalyticsService, HabitNotFoundError

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(
    session: AsyncSession = Depends(get_db),
) -> AnalyticsService:
    return AnalyticsService(session)


@router.get("/dashboard", response_model=DashboardResponseSchema)
async def get_dashboard(
    user_id: CurrentUserIdDep,
    service: AnalyticsService = Depends(get_analytics_service),
) -> DashboardResponseSchema:
    return await service.get_dashboard(user_id)


@router.get("/heatmap", response_model=HeatmapResponseSchema)
async def get_heatmap(
    user_id: CurrentUserIdDep,
    habit_id: uuid.UUID | None = Query(None),
    year: int = Query(
        default_factory=lambda: date.today().year,
        ge=2000,
        le=2100,
    ),
    service: AnalyticsService = Depends(get_analytics_service),
) -> HeatmapResponseSchema:
    try:
        return await service.get_heatmap(user_id, habit_id, year)
    except HabitNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
