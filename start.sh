#!/usr/bin/env bash
# local run
set -euo pipefail
cd "$(dirname "$0")"

SEED=0
RESET=0
for arg in "$@"; do
  case "$arg" in
    --include-synthetic) SEED=1 ;;
    --reset) RESET=1 ;;
    *) echo "Неизвестный флаг: $arg" >&2; echo "Доступные флаги: --include-synthetic, --reset" >&2; exit 1 ;;
  esac
done

if [[ ! -f .env ]]; then
  echo "Нет .env -> cp .env.example .env и заполните значения" >&2
  exit 1
fi

if [[ $RESET -eq 1 ]]; then
  docker compose down -v
fi

docker compose up -d --build

if [[ $SEED -eq 1 ]]; then
  docker compose --profile seed run --rm --build seed
fi

PORT=$(grep -E '^FRONTEND_PORT=' .env | cut -d= -f2 | tr -d '"' || true)
echo "Готово: http://localhost:${PORT:-8080}"