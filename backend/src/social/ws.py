import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from database.db import async_session_factory
from src.exceptions.social_exceptions import SocialError
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
from src.social.tickets import consume_ticket

logger = logging.getLogger(__name__)

router = APIRouter(tags=["💬 Chat WebSocket"])

# Какое событие каким классом разбирать (клиент → сервер).
_INCOMING_SCHEMAS = {
    "message": WSMessageIn,
    "history": WSHistoryIn,
    "mark_read": WSMarkReadIn,
}


class ConnectionManager:
    """
    Соединения в разбивке по пользователям.

    В браузере легко открыть несколько вкладок, поэтому на пользователя хранится
    набор соединений, а не одно: событие рассылается во все его вкладки.
    """

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        connections = self._connections.get(user_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: uuid.UUID, payload: dict) -> None:
        for websocket in list(self._connections.get(user_id, ())):
            try:
                await websocket.send_json(payload)
            except WebSocketDisconnect:
                self.disconnect(user_id, websocket)

    async def send_to_users(self, user_ids: set[uuid.UUID], payload: dict) -> None:
        for user_id in user_ids:
            await self.send_to_user(user_id, payload)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, ticket: str) -> None:
    """
    Один сокет на вкладку. Авторизация — одноразовым пропуском, полученным
    по REST-ручке /social/ws-ticket.

    Сессия БД открывается на каждое событие: соединение живёт долго, и держать
    из пула подключение всё это время нельзя.
    """
    user_id = await consume_ticket(ticket)
    if user_id is None:
        await websocket.close(code=4401)
        return

    await manager.connect(user_id, websocket)
    logger.info("WebSocket подключён: user=%s", user_id)
    try:
        while True:
            raw_event = await websocket.receive_json()
            await _handle_event(websocket, user_id, raw_event)
    except WebSocketDisconnect:
        logger.info("WebSocket отключён: user=%s", user_id)
    finally:
        manager.disconnect(user_id, websocket)


async def _handle_event(websocket: WebSocket, user_id: uuid.UUID, raw_event: dict) -> None:
    if not isinstance(raw_event, dict):
        await _send_error(websocket, "Событие должно быть объектом")
        return

    schema = _INCOMING_SCHEMAS.get(raw_event.get("type"))
    if schema is None:
        await _send_error(websocket, "Неизвестный тип события")
        return

    try:
        event = schema.model_validate(raw_event)
    except ValidationError as exc:
        detail = exc.errors()[0].get("msg", "Некорректное событие")
        await _send_error(websocket, str(detail))
        return

    try:
        async with async_session_factory() as session:
            service = SocialService(session)
            if isinstance(event, WSMessageIn):
                await _on_message(service, user_id, event)
            elif isinstance(event, WSHistoryIn):
                await _on_history(websocket, service, user_id, event)
            else:
                await _on_mark_read(service, user_id, event)
    except SocialError as exc:
        await _send_error(websocket, str(exc))
    except Exception:
        logger.exception("Ошибка обработки события WebSocket: user=%s", user_id)
        await _send_error(websocket, "Внутренняя ошибка")


async def _on_message(service: SocialService, user_id: uuid.UUID, event: WSMessageIn) -> None:
    message = await service.send_message(user_id, event.receiver_id, event.content)
    payload = WSNewMessageOut(message=message).model_dump(mode="json")
    # Отправляем и себе тоже: так отправитель получает подтверждение и id сообщения.
    await manager.send_to_users({user_id, event.receiver_id}, payload)


async def _on_history(
    websocket: WebSocket, service: SocialService, user_id: uuid.UUID, event: WSHistoryIn
) -> None:
    messages = await service.history(
        user_id, event.peer_id, limit=event.limit, before_id=event.before_id
    )
    payload = WSHistoryOut(peer_id=event.peer_id, messages=messages).model_dump(mode="json")
    await websocket.send_json(payload)


async def _on_mark_read(
    service: SocialService, user_id: uuid.UUID, event: WSMarkReadIn
) -> None:
    messages = await service.mark_read(user_id, event.message_ids)
    if not messages:
        return
    # Авторов прочитанных сообщений может быть несколько — оповещаем всех.
    authors = {message.sender_id for message in messages}
    payload = WSReadOut(by=user_id, message_ids=[message.id for message in messages]).model_dump(
        mode="json"
    )
    await manager.send_to_users(authors, payload)


async def _send_error(websocket: WebSocket, detail: str) -> None:
    await websocket.send_json(WSErrorOut(detail=detail).model_dump(mode="json"))
