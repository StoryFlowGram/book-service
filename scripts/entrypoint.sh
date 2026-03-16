#!/usr/bin/env sh
set -eu

cd /app

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}/app"

if [ "$#" -gt 0 ]; then
    echo "Запуск команди: $*"
    exec "$@"
fi

echo "Міграція"
alembic upgrade head

echo "Запуск API"
exec uvicorn main:app --host 0.0.0.0 --port 8000