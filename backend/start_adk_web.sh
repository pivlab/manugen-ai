#!/bin/bash

cd /opt/manugen-ai/src/

if [ -z "${SESSION_DB_CONN_STRING}" ]; then
    SESSION_DB_ARG=""
else
    SESSION_DB_ARG="--session_db_url ${SESSION_DB_CONN_STRING}"
fi

uv run --project /app \
     adk web --host 0.0.0.0 --port 8000 ${SESSION_DB_ARG}
