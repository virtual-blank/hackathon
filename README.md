# Хакатон

Трекер привычек с соцсетью: друзья, чат, достижения.

## Что нужно установить

- Docker с Docker Compose v2 (проверка: `docker compose version`)
- Git

## Первый запуск

```bash
git clone <адрес-репозитория>
cd hackathon

cp .env.example .env
chmod +x start.sh

./start.sh --include-synthetic
```

Первый запуск собирает образы и занимает несколько минут.

Когда в консоли появится `Готово`, откройте в браузере: **http://localhost:8080**

Флаг `--include-synthetic` заполняет базу демо-данными (пользователи, привычки, друзья, достижения). Без него приложение запустится с пустой базой.

### Демо-пользователи

Логины и пароли задаются в `.env` (переменные `SYNTHETIC_USER_1_*` и `SYNTHETIC_USER_2_*`). Войти можно под любым из них.

## Команды

| Что нужно | Команда |
|---|---|
| Запустить проект (данные сохраняются) | `./start.sh` |
| Запустить и заполнить демо-данными | `./start.sh --include-synthetic` |
| Стереть все данные и начать с нуля | `./start.sh --reset --include-synthetic` |
| Остановить проект (данные сохраняются) | `docker compose down` |
| Остановить и стереть все данные | `docker compose down -v` |
| Смотреть логи backend | `docker compose logs -f backend` |
| Пересобрать после изменения кода | `./start.sh` |

Повторный запуск с `--include-synthetic` безопасен: если демо-данные уже есть, скрипт их пропустит. Чтобы загрузить их заново, используйте `--reset`.

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