import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status, BackgroundTasks
from src.social.enums import RelationStatus
from src.achievements.service import AchievementsService
from src.auth.deps import CurrentUserIdDep, SessionDep
from src.exceptions.friends_exceptions import FriendsConflictError, FriendsNotFoundError
from src.friends.schemas import FriendRequestsSchema, FriendSchema, RelationStatusSchema
from src.friends.service import FriendsService

router = APIRouter(prefix="/friends", tags=["🤝 Friends"])

LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]


# == GET FRIENDS ==
@router.get("", response_model=list[FriendSchema], description="Список друзей")
async def get_friends(user_id: CurrentUserIdDep, session: SessionDep, limit: LimitQuery = 50, offset: OffsetQuery = 0):
    return await FriendsService(session=session).get_friends(user_id=user_id, limit=limit, offset=offset)


# == GET REQUESTS ==
@router.get("/requests", response_model=FriendRequestsSchema, description="Входящие и исходящие заявки")
async def get_requests(user_id: CurrentUserIdDep, session: SessionDep, limit: LimitQuery = 50):
    return await FriendsService(session=session).get_requests(user_id=user_id, limit=limit)


# == SEND REQUEST ==
@router.post(
    "/requests/{target_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=RelationStatusSchema,
    description="Отправить заявку. Если от этого пользователя уже есть встречная — она принимается",
)
async def send_request(target_id: uuid.UUID, user_id: CurrentUserIdDep, session: SessionDep, bt: BackgroundTasks):
    try:
        result = await FriendsService(session=session).send_request(user_id=user_id, target_id=target_id)
        if result.status == RelationStatus.ACCEPTED:
            bt.add_task(AchievementsService.process_achievements_friends_bt, user_id=user_id)
            bt.add_task(AchievementsService.process_achievements_friends_bt, user_id=target_id)
        return result
    except FriendsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FriendsConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


# == DECLINE REQUEST ==
@router.delete("/requests/{sender_id}", status_code=status.HTTP_204_NO_CONTENT, description="Отклонить входящую заявку")
async def decline_request(sender_id: uuid.UUID, user_id: CurrentUserIdDep, session: SessionDep) -> None:
    try:
        await FriendsService(session=session).decline_request(user_id=user_id, sender_id=sender_id)
    except FriendsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# == BLOCK USER ==
@router.post(
    "/blocks/{target_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=RelationStatusSchema,
    description="Заблокировать пользователя: заявки и дружба с ним удаляются",
)
async def block_user(target_id: uuid.UUID, user_id: CurrentUserIdDep, session: SessionDep):
    try:
        return await FriendsService(session=session).block_user(user_id=user_id, target_id=target_id)
    except FriendsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FriendsConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


# == ACCEPT REQUEST ==
@router.post(
    "/{sender_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=RelationStatusSchema,
    description="Принять входящую заявку",
)
async def accept_request(sender_id: uuid.UUID, user_id: CurrentUserIdDep, session: SessionDep, bt: BackgroundTasks):
    try:
        result = await FriendsService(session=session).accept_request(user_id=user_id, sender_id=sender_id)
        bt.add_task(AchievementsService.process_achievements_friends_bt, user_id=user_id)
        bt.add_task(AchievementsService.process_achievements_friends_bt, user_id=sender_id)
        return result
    except FriendsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# == DELETE FRIEND ==
@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT, description="Удалить из друзей")
async def delete_friend(friend_id: uuid.UUID, user_id: CurrentUserIdDep, session: SessionDep) -> None:
    try:
        await FriendsService(session=session).delete_friend(user_id=user_id, friend_id=friend_id)
    except FriendsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
