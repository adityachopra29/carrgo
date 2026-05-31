#!/bin/sh
set -e

mkdir -p data

if [ "$RUN_SEED" = "true" ]; then
  python seed.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
