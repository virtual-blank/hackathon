# Чаты: что реализовано в API

- **Ветка:** `dev/chat-api` (ответвлена от `dev/chat-schema-maks`)
- **Зона:** слои API модуля чатов — схемы, репозиторий, сервис, ручки
- **Модель данных:** одна таблица `messages` с полем `is_read` (решение Данила и Макса). Поля `is_read`, `read_at` и миграция уже сделаны Максом — здесь они только используются

---

## Что добавлено

| Файл | Содержимое |
|---|---|
| [`backend/src/social/schemas.py`](../backend/src/social/schemas.py) | шесть Pydantic-схем: создание и вывод сообщения, собеседник, строка списка диалогов, отметка прочтения, пропуск для вебсокета |
| [`backend/src/social/repository.py`](../backend/src/social/repository.py) | класс `SocialRepository`: только запросы к БД |
| [`backend/src/social/service.py`](../backend/src/social/service.py) | класс `SocialService`: проверки доступа и бизнес-логика |
| [`backend/src/social/router.py`](../backend/src/social/router.py) | `APIRouter` с префиксом `/api/social` и пять ручек |
| [`backend/src/social/tickets.py`](../backend/src/social/tickets.py) | одноразовые пропуска для вебсокета: `create_ticket`, `consume_ticket` |
| [`backend/src/exceptions/social_exceptions.py`](../backend/src/exceptions/social_exceptions.py) | кастомные исключения модуля |

Файлы `models.py`, [`backend/main.py`](../backend/main.py) и миграции **не менялись** — они пришли из ветки Макса.

---

## HTTP-ручки

Все ручки требуют авторизации: заголовок `Authorization: Bearer <JWT>`.
Префикс — `/api/social`.

### 1. Список диалогов

```
GET /api/social/chats
```

Возвращает диалоги пользователя, отсортированные по времени последнего сообщения.

```json
[
  {
    "peer": { "id": "0192...a1", "username": "boris" },
    "last_message_id": "0192...f7",
    "last_message_text": "Как дела?",
    "last_message_at": "2026-10-08T12:00:00Z",
    "unread_count": 2
  }
]
```

### 2. История диалога

```
GET /api/social/chats/{peer_id}/messages?limit=50&before_id=<uuid>
```

- сообщения идут **свежими первыми**;
- `limit` — от 1 до 100, по умолчанию 50;
- `before_id` — курсор: вернуть сообщения старше указанного (для листания вверх);
- порядок определяется полем `id`: UUIDv7 содержит время создания.

```json
[
  {
    "id": "0192...f7",
    "sender_id": "0192...b2",
    "receiver_id": "0192...a1",
    "content": "Как дела?",
    "created_at": "2026-10-08T12:00:00Z",
    "is_read": false,
    "read_at": null
  }
]
```

### 3. Отправить сообщение

```
POST /api/social/messages
{ "peer_id": "0192...a1", "content": "Привет" }
```

Ответ — объект сообщения, код `201`.

### 4. Отметить прочитанным

```
POST /api/social/chats/{peer_id}/read
{ "last_read_message_id": "0192...f7" }
```

Помечает прочитанным **всё**, что пришло от собеседника до указанного сообщения включительно. Ответ — `204` без тела.

### 5. Пропуск для вебсокета

```
POST /api/social/ws-ticket
```

```json
{ "ticket": "3Kx9...qA", "expires_in": 30 }
```

Пропуск одноразовый и живёт 30 секунд. Браузерный WebSocket не умеет передавать заголовок авторизации, поэтому клиент получает пропуск по REST и предъявляет его при подключении.

---

## Коды ошибок

| Ситуация | Ответ |
|---|---|
| Переписка с самим собой | `400` |
| Не друзья (нет статуса `accepted` в `user_relations`) | `403` |
| Один из пользователей заблокирован | `403` |
| Сообщения нет или оно адресовано не мне | `404` |
| Не передан или просрочен токен | `401` |

Перевод ошибок живёт в одном месте — словарь `_ERROR_STATUS` и функция `_to_http_error` в роутере.

---

## Правила доступа

- Переписка доступна **только друзьям**: статус `accepted` в [`user_relations`](../backend/src/social/models.py).
- Если между пользователями есть блокировка (`blocked`) — доступа нет, ответ `403`.
- Писать самому себе нельзя.
- Проверки выполняются в сервисе, роутер и репозиторий их не содержат.

---

## Как считаются прочтение и непрочитанные

Отдельного счётчика в базе нет — всё выводится из поля `is_read`.

**Непрочитанные от собеседника:**

```sql
SELECT count(*) FROM messages
WHERE receiver_id = :me AND sender_id = :peer AND is_read = false;
```

**Отметка прочтения** (в репозитории — метод `mark_read`):

```sql
UPDATE messages
SET is_read = true, read_at = now()
WHERE receiver_id = :me AND sender_id = :peer
  AND id <= :last_read_message_id AND is_read = false;
```

**Список диалогов** собирается двумя запросами:

1. последнее сообщение по каждому собеседнику — оконная функция `row_number()` с разбиением по собеседнику;
2. количество непрочитанных — группировка по `sender_id` одним запросом.

Название собеседника подтягивается одним запросом по списку его id, без обращения к базе на каждый диалог.

---

## Стык с вебсокетами (зона Макса)

Сервис отдаёт наружу эти методы — `ws.py` вызывает их напрямую:

| Метод | Зачем |
|---|---|
| `send_message(me, peer_id, content)` | сохранить сообщение и вернуть его DTO |
| `history(me, peer_id, limit, before_id)` | отдать историю по сокету, если нужно |
| `mark_read(me, peer_id, last_read_message_id)` | отметить прочтение по событию клиента |
| `list_chats(me)` | список диалогов |
| `issue_ws_ticket(me)` | выдать пропуск (используется ручкой, не сокетом) |

Для проверки пропуска при подключении:

```python
from src.social.tickets import consume_ticket

user_id = consume_ticket(ticket)   # None, если пропуск неверный или просрочен
```

В событиях `new_message` и `read` стоит передавать `peer_id`, `message_id`, `is_read` и время — иначе фронт не отрисует ни сообщение, ни галочку.

---

## Что ещё не сделано

- **Роутер не подключён в приложении.** В [`backend/main.py`](../backend/main.py) есть пометка автора: подключение роутеров ждёт переименования `hash-argon.py` → `hash_argon.py`, иначе импорт падает.
- **Тесты** не написаны: нужны на доступ (друзья и блокировка), порядок сообщений, подсчёт непрочитанных и отметку прочтения.
- **Индексы.** В модели есть `ix_messages_dialog (sender_id, receiver_id, id)` и `ix_messages_is_read`. Для обратного направления диалога полезен парный индекс `(receiver_id, sender_id, id)`, а для подсчёта непрочитанных — составной `(receiver_id, is_read)`. Это правка модели и миграции Макса, поэтому её надо с ним согласовать.
- **Неиспользуемые методы:** `get_user` и `count_unread` в репозитории пока никто не вызывает — либо уберём, либо они пойдут под ручку `unread_count`.

---

## Как запустить

```bash
cd backend
poetry install
alembic upgrade head
uvicorn main:app --reload
```

Проверка, что сервер поднялся: `GET /health` → `{"status": "ok"}`.
Документация ручек: `/docs`.

Пока не исправлено имя файла [`hash-argon.py`](../backend/src/auth/hash-argon.py) (дефис ломает импорт), приложение поднимется только с закомментированным подключением `users_router`, как сейчас в `main.py`.
