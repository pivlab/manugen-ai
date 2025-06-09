#!/bin/bash

cd /opt/manugen-ai/src/

uv run --project /app \
     adk web --host 0.0.0.0 --port 8000
