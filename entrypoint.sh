#!/usr/bin/sh
set -e

echo "Starting application"
exec gunicorn app.main:app \
  -w 1 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
