#!/bin/sh
set -e

exec gunicorn \
    -k uvicorn.workers.UvicornWorker \
    --workers 1 \
    --threads 4 \
    --bind 0.0.0.0:8000 \
    --log-level=INFO \
    $GUNICORN_CMD_ARGS \
    idp_schedule_provider.main:app
