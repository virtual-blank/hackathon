import uuid

from fastapi import APIRouter, HTTPException, Query, status

from src.auth.deps import CurrentUserDep, SessionDep
from src.exceptions.social_exceptions import (
    ChatWithSelfError,
    MessageNotFoundError,
    NotFriendsError,
    SocialError,
    UserBlockedError,
)
from src.social.schemas import (
    ChatOutputSchema,
    MessageCreateSchema,
    MessageOutputSchema,
    ReadMessageSchema,
    WsTicketSchema,
)
from src.social.service import SocialService

router = APIRouter(prefix="/api/social", tags=["💬 Social"])

# Ошибки сервиса -> коды ответа. Роутер только переводит, логики не содержит.
_ERROR_STATUS: dict[type[SocialError], int] = {
    ChatWithSelfError: status.HTTP_400_BAD_REQUEST,
    NotFriendsError: status.HTTP_403_FORBIDDEN,
    UserBlockedError: status.HTTP_403_FORBIDDEN,
    MessageNotFoundError: status.HTTP_404_NOT_FOUND,
}


def _to_http_error(exc: SocialError) -> HTTPException:
    code = _ERROR_STATUS.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return HTTPException(status_code=code, detail=str(exc))


# == LIST CHATS ==
@router.get(
    "/chats",
    response_model=list[ChatOutputSchema],
    description="Список диалогов с последним сообщением и числом непрочитанных",
)
async def list_chats(user: CurrentUserDep, session: SessionDep):
    return await SocialService(session).list_chats(user.id)


# == HISTORY ==
@router.get(
    "/chats/{peer_id}/messages",
    response_model=list[MessageOutputSchema],
    description="История диалога: свежие первыми, before_id — курсор вверх",
)
async def history(
    peer_id: uuid.UUID,
    user: CurrentUserDep,
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=100),
    before_id: uuid.UUID | None = Query(default=None),
):
    try:
        return await SocialService(session).history(
            user.id, peer_id, limit=limit, before_id=before_id
        )
    except SocialError as exc:
        raise _to_http_error(exc) from exc


# == SEND MESSAGE ==
@router.post(
    "/messages",
    response_model=MessageOutputSchema,
    status_code=status.HTTP_201_CREATED,
    description="Отправить сообщение собеседнику",
)
async def send_message(
    payload: MessageCreateSchema, user: CurrentUserDep, session: SessionDep
):
    try:
        return await SocialService(session).send_message(user.id, payload.peer_id, payload.content)
    except SocialError as exc:
        raise _to_http_error(exc) from exc


# == MARK READ ==
@router.post(
    "/chats/{peer_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Отметить прочитанным всё от собеседника до указанного сообщения",
)
async def mark_read(
    peer_id: uuid.UUID,
    payload: ReadMessageSchema,
    user: CurrentUserDep,
    session: SessionDep,
):
    try:
        await SocialService(session).mark_read(user.id, peer_id, payload.last_read_message_id)
    except SocialError as exc:
        raise _to_http_error(exc) from exc


# == WS TICKET ==
@router.post(
    "/ws-ticket",
    response_model=WsTicketSchema,
    description="Одноразовый пропуск для подключения к вебсокету",
)
async def ws_ticket(user: CurrentUserDep, session: SessionDep):
    return await SocialService(session).issue_ws_ticket(user.id)
