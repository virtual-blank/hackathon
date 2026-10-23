# analogovnet.rest

[Веб приложение доступно по ссылке](https://analogovnet.rest)  (vpn)

### **Социальная сеть для совместного трекинга привычек, в которой есть:**

- Система стриков и достижений
- Дашборд с визуализацией и подробными метриками
- Система друзей
- Чаты
- Новостная лента
- Интеграция с Telegram для уведомлений
- Экспорт статистики в .csv
- Настройка личного профиля
***


### 🖼️ Screenshots

<img width="1894" height="904" alt="{D2FAD369-A99D-4B15-A754-377C3E3CF692}" src="https://github.com/user-attachments/assets/b6b21893-e1a8-4164-9e57-4d5bce25bcf6" />
<img width="1890" height="896" alt="{6A5B89F8-5D2B-4D7A-8147-2E7BAC984859}" src="https://github.com/user-attachments/assets/6c8bb821-cbb9-40c5-8540-3e68276bbafa" />
<img width="1890" height="902" alt="{FCF3171A-F19E-459B-BEEE-38B785F0FF63}" src="https://github.com/user-attachments/assets/8889ee3b-23ae-4c3b-8a5b-0c07f1eecb8d" />
<img width="1892" height="896" alt="{B606B5E5-E673-4C0C-8494-76C78C68D376}" src="https://github.com/user-attachments/assets/1844ac91-fbff-45e6-96e1-d71158477a97" />
<img width="1916" height="908" alt="{6D648703-4E78-4FD8-8A97-9584182BB8BB}" src="https://github.com/user-attachments/assets/9279209b-c871-486f-b331-134b162887d3" />
<img width="1915" height="902" alt="{7052B86B-E306-4440-B493-DDB89F7DBCD9}" src="https://github.com/user-attachments/assets/7519c29c-e03b-41f1-ae62-f6d6f63df56d" />


***

# Установка

### Требования:

- Docker с Docker Compose v2 (проверка: `docker compose version`)
- Git
- Свободные порты: `8080` (приложение), `9000` и `9001` (MinIO), `5435` (Postgres)

Docker Desktop не обязателен: на macOS достаточно `colima` (`brew install colima docker docker-compose`, затем `colima start`).
После установки из Homebrew плагину compose нужен путь в `~/.docker/config.json`:

```json
{ "cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"] }
```

## Подготовка (один раз)

Клонирование репозитория:

```bash
git clone git@github.com:virtual-blank/hackathon.git
cd hackathon
```

Если SSH-ключ в GitHub не настроен, клонируйте по HTTPS:

```bash
git clone https://github.com/virtual-blank/hackathon.git
```

Создание `.env` из шаблона:

```bash
cp .env.example .env
```

Значения из шаблона подходят для локального запуска как есть — менять ничего не нужно. Этот единственный `.env` читают все сервисы: Postgres, backend, seed и MinIO, поэтому переменные вида `MINIO_PUBLIC_URL` попадают в ссылки на аватарки, а `POSTGRES_*` — в строку подключения.

Скрипт запуска должен быть исполняемым:

```bash
chmod +x start.sh
```

## Локальный запуск

Оба сценария используют один и тот же `start.sh`; разница только в флаге. Скрипт делает три вещи: собирает образы, поднимает контейнеры и, если попросили, заливает демо-данные.

### Сценарий 1 — пустая база (только миграции)

```bash
./start.sh
```

Что происходит по шагам:

1. `docker compose up -d --build` — собираются образы и поднимаются `postgres`, `minio`, `backend`, `frontend`.
2. Backend при старте применяет миграции: `python -m alembic upgrade head` в `backend/docker-entrypoint.sh`, то есть схема БД создаётся автоматически, руками ничего накатывать не нужно.
3. Демо-данных нет: таблицы пустые. Пользователя нужно создать самому — через форму регистрации в интерфейсе или `POST /api/v1/users/sign-up`.

Подходит, когда нужно посмотреть приложение «с чистого листа» или проверить регистрацию.

### Сценарий 2 — база с демо-данными (миграции + синтетика)

```bash
./start.sh --include-synthetic
```

Шаги те же, плюс четвёртый:

4. После того как backend стал `healthy`, запускается разовый контейнер из профиля `seed` (`docker compose --profile seed run --rm --build seed`), который выполняет `python -m src.synthetic.fill_db`. В базу попадают пользователи, привычки, отметки, друзья, переписки, отзывы и достижения — порядка 700 тыс. записей:

```
[!] Записи в БД:
  achievements                10
  users                  ~2,8 тыс.
  habits                  ~13 тыс.
  user_relations          ~41 тыс.
  messages                ~95 тыс.
  habit_logs             ~535 тыс.
```

Точные числа зависят от генератора и при каждом заполнении разные.

### Флаги `start.sh`

| Команда | Что делает |
|---|---|
| `./start.sh` | миграции + пустая база |
| `./start.sh --include-synthetic` | миграции + демо-данные |
| `./start.sh --reset` | стирает тома `pg_data` и `minio_data` (`docker compose down -v`), затем миграции + пустая база |
| `./start.sh --reset --include-synthetic` | стереть всё и залить демо-данные заново |

- `--reset` комбинируется с `--include-synthetic`, порядок флагов не важен: сначала удаляются данные, потом идёт обычный запуск.
- Неизвестный флаг скрипт не игнорирует — останавливается с ошибкой и списком допустимых.
- Повторный запуск с `--include-synthetic` безопасен: если демо-пользователи уже есть, seed пропускается (`Demo data already loaded… Skipping`). Чтобы залить их заново, нужен `--reset`.
- Первый запуск собирает образы и занимает несколько минут: `poetry install` для backend, `npm ci` и `vite build` для frontend, а MinIO и `mc` собираются из исходников на Go. Повторные запуски используют кэш и занимают секунды.

Когда в консоли появится `Готово: http://localhost:8080` — приложение готово, открывайте **http://localhost:8080**.

### Демо-пользователи

Появляются только после `--include-synthetic`. Логины и пароли задаются в `.env` (`SYNTHETIC_USER_1_*`, `SYNTHETIC_USER_2_*`), по умолчанию:

| Логин | Пароль |
|---|---|
| `user_1` | `password` |
| `user_2` | `password` |

Вход выполняется **по логину (`username`), а не по email** — `POST /api/v1/users/login` с полями `username` и `password`.

## Повседневные команды

Запуск и флаги `start.sh` — в разделе «Локальный запуск» выше. Здесь — что делать с уже запущенным проектом.

| Что нужно | Команда |
|---|---|
| Остановить проект (данные сохраняются) | `docker compose down` |
| Остановить и стереть все данные | `docker compose down -v` |
| Пересобрать после изменения кода | `./start.sh` |
| Смотреть логи backend | `docker compose logs -f backend` |
| Смотреть логи всех сервисов | `docker compose logs -f` |
| Состояние контейнеров | `docker compose ps` |
| Зайти в psql | `docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_NAME"'` |

## Адреса

| Что | Адрес |
|---|---|
| Приложение | http://localhost:8080 |
| Документация API (Swagger) | http://localhost:8080/docs |
| Консоль MinIO (файлы) | http://localhost:9001 |
| Postgres | localhost:5435 |

Логин и пароль консоли MinIO: `MINIO_ROOT_USER` и `MINIO_ROOT_PASSWORD` из `.env`.

## Если что-то не работает

**`permission denied: ./start.sh`**
```bash
chmod +x start.sh
```

**Порт 8080 занят.** Поменяйте `FRONTEND_PORT` в `.env` на свободный и запустите снова.

**Не показываются аватарки.** В `.env` должно быть `MINIO_PUBLIC_URL="http://localhost:9000"`. После изменения сотрите данные и загрузите их заново:
```bash
./start.sh --reset --include-synthetic
```

**Что-то сломалось после обновления кода.** Начните с чистого листа:
```bash
./start.sh --reset --include-synthetic
```

**Посмотреть, какие контейнеры запущены и в каком они состоянии:**
```bash
docker compose ps
```

## Разработка

Backend можно запускать на своём компьютере, а не в Docker. Для этого нужны Python 3.12 и Poetry.

```bash
docker compose up -d postgres minio minio-init   # база и файловое хранилище
make install                                      # зависимости
make hooks                                        # git-хуки (один раз)
make migrate                                      # миграции
make run                                          # API на http://localhost:8000
```

Остальные команды: `make help`.

## Запуск на сервере

Для сервера нужен отдельный `.env`:

- `MINIO_PUBLIC_URL="https://ваш-домен"`
- `TELEGRAM_WEBHOOK_URL="https://ваш-домен/api/v1/telegram/webhook"`
- `FRONTEND_BIND="0.0.0.0"`, `FRONTEND_PORT="80"`
- `CLOUDFLARE_TUNNEL_TOKEN="..."`

Запуск с туннелем Cloudflare:
```bash
docker compose --profile tunnel up -d --build
```
