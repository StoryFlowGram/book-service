#!/bin/sh
set -e

export PYTHONPATH=$PYTHONPATH:.

echo "Запуск миграций"
poetry run alembic upgrade head

echo "Запуск Uvicorn"
exec poetry run uvicorn main:app --host 0.0.0.0 --port 8000