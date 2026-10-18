import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from database.db import async_session_factory
from src.auth.security import decode_access_token
from src.exceptions.auth_exceptions import InvalidTokenError
from src.social.schemas import (
    WSErrorOut,
    WSHistoryIn,
    WSHistoryOut,
    WSMarkReadIn,
    WSMessageIn,
    WSNewMessageOut,
    WSReadOut,
)
from src.social.service import SocialService

router = APIRouter()


class ConnectionManager:
    """
    Реестр активных WebSocket-соединений в памяти процесса.
    user_id → множество сокетов (у юзера может быть несколько вкладок/устройств).
    """

    def __init__(self) -> None:
        self.active: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        sockets = self.active.get(user_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self.active.pop(user_id, None)

    async def send_to_user(self, user_id: uuid.UUID, payload: dict) -> bool:
        """
        Отправить payload во все сокеты юзера.
        True — если доставлено (юзер онлайн), False — если офлайн.
        """
        sockets = self.active.get(user_id)
        if not sockets:
            return False
        # копия: сокет может отвалиться во время итерации
        for websocket in list(sockets):
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(user_id, websocket)
        return True


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint для чата.
    Аутентификация — JWT в query-параметре: /ws/chat?token=<JWT>.
    """
    # == АУТЕНТИФИКАЦИЯ ==
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Токен не передан")
        return

    try:
        user_id = decode_access_token(token)
    except InvalidTokenError as exc:
        await websocket.close(code=1008, reason=str(exc))
        return

    # == РЕГИСТРАЦИЯ В МЕНЕДЖЕРЕ ==
    await manager.connect(user_id, websocket)

    try:
        # == ЦИКЛ ОБРАБОТКИ СОБЫТИЙ ==
        while True:
            try:
                raw = await websocket.receive_json()
                if not isinstance(raw, dict):
                    raise ValueError
                await _handle_event(user_id, raw, websocket)
            except WebSocketDisconnect:
                raise
            except Exception:
                await websocket.send_json(WSErrorOut(detail="Некорректное событие").model_dump())
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)


async def _handle_event(user_id: uuid.UUID, raw: dict, websocket: WebSocket) -> None:
    """Роутинг события по полю `type`."""
    event_type = raw.get("type")

    if event_type == "message":
        await _handle_message(user_id, raw, websocket)
    elif event_type == "history":
        await _handle_history(user_id, raw, websocket)
    elif event_type == "mark_read":
        await _handle_mark_read(user_id, raw, websocket)
    else:
        await websocket.send_json(WSErrorOut(detail=f"Неизвестный тип события: {event_type}").model_dump())


async def _handle_message(user_id: uuid.UUID, raw: dict, websocket: WebSocket) -> None:
    """Событие `message`: сохранить и запушить получателю."""
    try:
        payload = WSMessageIn.model_validate(raw)
    except ValidationError as exc:
        await websocket.send_json(WSErrorOut(detail=str(exc)).model_dump())
        return

    async with async_session_factory() as session:
        service = SocialService(session=session)
        try:
            message = await service.send_message(
                sender_id=user_id,
                receiver_id=payload.receiver_id,
                content=payload.content,
            )
        except ValueError as exc:
            await websocket.send_json(WSErrorOut(detail=str(exc)).model_dump())
            return

    # пуш получателю, если онлайн
    await manager.send_to_user(
        payload.receiver_id,
        WSNewMessageOut(message=message).model_dump(mode="json"),
    )

    # эхо отправителю — подтверждение, что сообщение сохранено
    await websocket.send_json(WSNewMessageOut(message=message).model_dump(mode="json"))


async def _handle_history(user_id: uuid.UUID, raw: dict, websocket: WebSocket) -> None:
    """Событие `history`: отдать историю переписки с собеседником."""
    try:
        payload = WSHistoryIn.model_validate(raw)
    except ValidationError as exc:
        await websocket.send_json(WSErrorOut(detail=str(exc)).model_dump())
        return

    async with async_session_factory() as session:
        service = SocialService(session=session)
        try:
            messages = await service.get_history(
                user_id=user_id,
                peer_id=payload.peer_id,
                limit=payload.limit,
                before_id=payload.before_id,
            )
        except ValueError as exc:
            await websocket.send_json(WSErrorOut(detail=str(exc)).model_dump())
            return

    await websocket.send_json(WSHistoryOut(peer_id=payload.peer_id, messages=messages).model_dump(mode="json"))


async def _handle_mark_read(user_id: uuid.UUID, raw: dict, websocket: WebSocket) -> None:
    """Событие `mark_read`: пометить сообщения прочитанными и уведомить отправителей."""
    try:
        payload = WSMarkReadIn.model_validate(raw)
    except ValidationError as exc:
        await websocket.send_json(WSErrorOut(detail=str(exc)).model_dump())
        return

    async with async_session_factory() as session:
        service = SocialService(session=session)
        updated = await service.mark_as_read(
            message_ids=payload.message_ids,
            reader_id=user_id,
        )

    if not updated:
        return

    # уведомить каждого отправителя: его сообщения прочитаны
    message_ids_by_sender: dict[uuid.UUID, list[uuid.UUID]] = {}
    for message in updated:
        message_ids_by_sender.setdefault(message.sender_id, []).append(message.id)

    for sender_id, message_ids in message_ids_by_sender.items():
        await manager.send_to_user(
            sender_id,
            WSReadOut(by=user_id, message_ids=message_ids).model_dump(mode="json"),
        )


# == ПОДКЛЮЧЕНИЕ В main.py ==
# from src.social.ws import router as social_ws_router
# app.include_router(social_ws_router)   # БЕЗ /api/v1 — WS обычно отдельно
