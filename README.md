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

## Первый запуск

Клонирование репозитория:
```bash
git clone https://github.com/virtual-blank/hackathon.git
```
```bash
cd hackathon
```
Заполнение .env
```bash
cp .env.example .env
```
```bash
chmod +x start.sh
```
Запуск со сгенерированной базой данных (700тыс+):
```bash
./start.sh --include-synthetic
```
```
[!] Записи в БД:
  achievements                10
  users                    2,889
  refresh_tokens           4,508
  reviews                 10,447
  user_achievements       20,694
  habits                  12,987
  user_relations          41,046
  messages                95,281
  habit_logs             542,998
```
Запуск с пустой базой данных:
```bash
./start.sh
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
