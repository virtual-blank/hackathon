# Чаты: что реализовано

- **Ветка:** `dev/chat-api`
- **Префикс:** в [`main.py`](../backend/main.py) роутеры подключаются с `ROUTERS_PREFIX = "/api/v1"`, у модуля чатов свой префикс `/social`. Итоговые пути — `/api/v1/social/...`
- **Схема данных:** одна таблица `messages` с флагом `is_read` (решение Данила и Макса)

---

## Что было и что добавлено

В базе уже лежали [`schemas.py`](../backend/src/social/schemas.py) с HTTP- и WS-схемами и [`repository.py`](../backend/src/social/repository.py) с классом `MessagesRepository`. В этой ветке дописано то, чего не хватало:

| Файл | Что добавлено |
|---|---|
| [`schemas.py`](../backend/src/social/schemas.py) | `MarkReadSchema`, `ChatPeerSchema`, `ChatOutputSchema`, `WsTicketSchema` |
| [`repository.py`](../backend/src/social/repository.py) | `get_last_messages` (последнее сообщение по собеседникам), `count_unread_by_peers`, `get_users`, `are_friends`, `is_blocked_between` |
| [`service.py`](../backend/src/social/service.py) | бизнес-логика: проверки доступа, отправка, история, отметка прочтения |
| [`router.py`](../backend/src/social/router.py) | HTTP-ручки |
| [`ws.py`](../backend/src/social/ws.py) | `ConnectionManager` и обработчик WebSocket-событий |
| [`tickets.py`](../backend/src/social/tickets.py) | одноразовые пропуска для сокета, теперь в Redis |
| [`../backend/database/redis.py`](../backend/database/redis.py) | клиент Redis |
| [`../backend/core/config.py`](../backend/core/config.py) | `RedisSettings` (`REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`) |

---

## HTTP-ручки

Авторизация — заголовок `Authorization: Bearer <JWT>`.

| Метод | Путь | Что делает | Ответ |
|---|---|---|---|
| GET | `/api/v1/social/chats` | список диалогов: собеседник, последнее сообщение, непрочитанные | `200` |
| GET | `/api/v1/social/chats/{peer_id}/messages?limit&before_id` | история, свежие первыми, `before_id` — курсор вверх | `200` |
| POST | `/api/v1/social/messages` | отправить: `{"receiver_id": "...", "content": "..."}` | `201` |
| POST | `/api/v1/social/messages/read` | отметить прочитанными: `{"message_ids": ["..."]}` | `200` |
| POST | `/api/v1/social/ws-ticket` | одноразовый пропуск для сокета | `200` |

Пример ответа списка диалогов:

```json
[
  {
    "peer": { "id": "0192...a1", "username": "boris" },
    "last_message_id": "0192...f7",
    "last_message_text": "Как дела?",
    "last_message_at": "2026-10-12T12:00:00Z",
    "unread_count": 2
  }
]
```

---

## Коды ошибок

| Ситуация | Ответ |
|---|---|
| Переписка с самим собой | `400` |
| Не друзья (нет статуса `accepted` в `user_relations`) | `403` |
| Есть блокировка в любую сторону | `403` |
| Нет или просрочен токен | `401` |

Перевод ошибок живёт в одном месте: словарь `_ERROR_STATUS` и функция `_to_http_error` в [`router.py`](../backend/src/social/router.py).

---

## WebSocket

### Подключение

1. Клиент получает пропуск: `POST /api/v1/social/ws-ticket` → `{"ticket": "...", "expires_in": 30}`.
2. Подключается: `ws://<host>/api/v1/ws/chat?ticket=<ticket>`.

Пропуск **одноразовый** и лежит в Redis с автоистечением — за счёт этого приложение можно запускать в несколько воркеров: пропуск, выданный одним процессом, примет любой другой. Заголовок авторизации тут не нужен, потому что браузерный `WebSocket` его передавать не умеет.

### События от клиента

| `type` | Поля |
|---|---|
| `message` | `receiver_id`, `content` |
| `history` | `peer_id`, `limit` (до 200, по умолчанию 50), `before_id` |
| `mark_read` | `message_ids` (непустой список) |

### События от сервера

| `type` | Поля |
|---|---|
| `new_message` | `message` — объект сообщения |
| `history` | `peer_id`, `messages` |
| `read` | `by` (кто прочитал), `message_ids` |
| `error` | `detail` |

Отправитель получает `new_message` вместе с адресатом — так он узнаёт id своего сообщения.

---

## Правила доступа

- Переписка доступна только друзьям: статус `accepted` в `user_relations`.
- Блокировка в любую сторону закрывает переписку обоим.
- Писать самому себе нельзя.
- Отметить прочитанным можно только сообщения, адресованные тебе: репозиторий фильтрует по `receiver_id`, чужие id просто игнорируются.

---

## Как считаются прочтение и непрочитанные

Отдельного счётчика в базе нет, всё выводится из `is_read`.

**Непрочитанные по собеседникам** (`count_unread_by_peers`) — один запрос на весь список диалогов:

```sql
SELECT sender_id, count(*) FROM messages
WHERE receiver_id = :me AND is_read = false
GROUP BY sender_id;
```

**Отметка прочтения** (`mark_messages_read`): обновляем только свои сообщения, `read_at` ставится на стороне приложения.

**Список диалогов** (`get_last_messages`): последнее сообщение по каждому собеседнику через оконную функцию `row_number()`; имена собеседников подтягиваются одним запросом `get_users`, чтобы не было запроса на каждый диалог.

---

## Менеджер соединений

`ConnectionManager` в [`ws.py`](../backend/src/social/ws.py) хранит **набор** соединений на пользователя (`dict[user_id, set[WebSocket]]`), а не одно: в браузере легко открыть несколько вкладок, и событие должно уйти во все. При разрыве вкладка убирается из набора, пустой набор удаляется.

Сессия БД открывается на каждое событие, а не на всё время жизни сокета: соединение живёт долго, и держать подключение из пула всё это время нельзя.

---

## Что нужно сделать команде

- **Redis в зависимостях.** В [`pyproject.toml`](../backend/pyproject.toml) добавлен `redis = ">=5.0"`, но `poetry.lock` обновить не получилось — poetry в окружении нет. Нужно выполнить `make lock` (или `poetry lock`) и закоммитить `pyproject.toml` вместе с `poetry.lock`, как договаривались: отдельным коммитом `add: redis`.
- **Запуск для проверки:**

```bash
cp .env.example .env      # при необходимости поправить REDIS_*
docker compose up -d postgres redis
cd backend && poetry install && alembic upgrade head && uvicorn main:app --reload
```

---

## Что ещё не сделано

- **Тесты** не написаны: нужны на доступ (друзья и блокировка), порядок сообщений, подсчёт непрочитанных, отметку прочтения.
- **Индексы.** В модели есть `ix_messages_dialog (sender_id, receiver_id, id)` и `ix_messages_is_read`. Для обратного направления диалога полезен парный индекс `(receiver_id, sender_id, id)`, а под подсчёт непрочитанных — составной `(receiver_id, is_read)`: индекс по одному булеву полю почти не используется планировщиком. Это правка модели и миграции Макса, поэтому её надо согласовать.
- **Проверка дружбы при блокировке** опирается на таблицу `user_relations`, которую заполняет модуль соцсвязей — пока ручек дружбы нет, тестировать чат получится только на подготовленных данных.
