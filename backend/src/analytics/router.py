import uuid

from fastapi import APIRouter, HTTPException, Query, status

from src.analytics.schemas import DashboardOutputSchema
from src.analytics.service import AnalyticsService
from src.auth.deps import CurrentUserDep, SessionDep
from src.friends.repository import FriendsRepository
from src.habits.enums import Visibility
from src.social.enums import RelationStatus
from src.users.models import User

router = APIRouter(prefix="/analytics", tags=["📊 Analytics"])


@router.get(
    "/dashboard",
    response_model=DashboardOutputSchema,
    status_code=status.HTTP_200_OK,
    description="Получить полную аналитику и Plotly-графики для дашборда",
)
async def get_dashboard(
    current_user: CurrentUserDep,
    session: SessionDep,
    target_user_id: uuid.UUID | None = Query(
        default=None,
        description="ID пользователя (если не указан — возвращается дашборд текущего пользователя)",
    ),
    activity_days: int = Query(
        default=30,
        ge=7,
        le=365,
        description="За сколько последних дней строить график активности",
    ),
):
    target_user = current_user
    visibilities: list[Visibility] | None = None

    if target_user_id is not None and target_user_id != current_user.id:
        friends_repo = FriendsRepository(session=session)
        relations = await friends_repo.get_pair_relations(
            first_id=current_user.id,
            second_id=target_user_id,
        )

        is_blocked = any(r.status == RelationStatus.BLOCKED for r in relations)
        if is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ к аналитике пользователя запрещён",
            )

        target_user = await session.get(User, target_user_id)
        if target_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        is_friend = any(r.status == RelationStatus.ACCEPTED for r in relations)
        if is_friend:
            visibilities = [Visibility.FRIENDS, Visibility.PUBLIC]
        else:
            visibilities = [Visibility.PUBLIC]

    service = AnalyticsService(session=session)
    return await service.get_dashboard(
        user=target_user,
        activity_days=activity_days,
        visibilities=visibilities,
    )
