# Хакатон [dev]

# Первый запуск:

В корне проекта /hackathon собираете и запускаете контейнер:

```bash
docker compose up -d --build
```
 В **/hackathon/backend** накатываете миграции:

 ```bash
poetry run alembic upgrade head
 ```

- Если alembic отдал ошибки и не можете решить: пишите мне

- Если все ок: оставаясь в /hackathon/backend запускаете мейн как модуль:

```bash
poetry run python -m main
```
***

# Повторный запуск (если бд уже есть):

В **/hackathon**

```bash
docker compose up -d
```

В **/hackathon/backend**

```bash
poetry run python -m main
```
# Полезные команды:

Удалить контейнер и бд:
```bash
docker compose down -v
```

