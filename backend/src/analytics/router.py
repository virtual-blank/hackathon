import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import HTMLResponse

from database.db import get_db
from src.auth.deps import CurrentUserIdDep
from src.analytics.schemas import DashboardResponseSchema, HeatmapResponseSchema
from src.analytics.service import AnalyticsService, HabitNotFoundError
from src.analytics.dashboard import render_dashboard_html
from src.analytics.schemas import HabitPattern


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


@router.get("/view", response_class=HTMLResponse)
async def analytics_view(
    user_id: CurrentUserIdDep,
    year: int = Query(default_factory=lambda: date.today().year, ge=2000, le=2100),
    service: AnalyticsService = Depends(get_analytics_service),
):
    dashboard = await service.get_dashboard(user_id)
    heatmap = await service.get_heatmap(user_id, None, year)
    patterns = await service.get_weekday_patterns(user_id)
    html = render_dashboard_html(dashboard, heatmap, patterns, year)
    return HTMLResponse(content=html)


@router.get("/weekday", response_model=list[HabitPattern])
async def get_weekday_patterns(
    user_id: CurrentUserIdDep,
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[HabitPattern]:
    return await service.get_weekday_patterns(user_id)
