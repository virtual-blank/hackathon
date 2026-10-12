.PHONY: help install lock run lint fix format migrate migration hooks

# Poetry-проект лежит в backend/, поэтому команды выполняются оттуда.
BACKEND := cd backend &&

help: ## Показать справку по командам
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости через Poetry
	$(BACKEND) poetry install

lock: ## Пересобрать poetry.lock после ручной правки pyproject.toml
	$(BACKEND) poetry lock

run: ## Запустить API-сервер с авто-перезагрузкой
	$(BACKEND) poetry run fastapi dev main.py

lint: ## Проверить код линтером, ничего не меняя
	$(BACKEND) poetry run ruff check .

fix: ## Исправить то, что линтер умеет чинить сам
	$(BACKEND) poetry run ruff check --fix .

format: ## Отформатировать код
	$(BACKEND) poetry run ruff format .

migrate: ## Применить миграции до head
	$(BACKEND) poetry run alembic upgrade head

m ?=

migration: ## Создать миграцию по изменениям моделей (m="описание")
	@test -n "$(m)" || (echo 'Нужно описание: make migration m="add avatar key"' && exit 1)
	$(BACKEND) poetry run alembic revision --autogenerate -m "$(m)"

hooks: ## Подключить git hooks из .githooks (один раз после клонирования)
	git config core.hooksPath .githooks