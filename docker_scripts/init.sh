#!/bin/sh
FASTAPI_APP=idp_schedule_provider.main:app

exec uvicorn "$FASTAPI_APP" \
    --host 0.0.0.0 \
    --port 8000 \
    $UVICORN_CMD_ARGS
