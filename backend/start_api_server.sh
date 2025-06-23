#!/bin/bash

# Start a FastAPI server implementing the Manugen AI Backend

MANUGEN_API_PORT=${MANUGEN_API_PORT:-8000}

echo "Starting Manugen AI Backend on http://0.0.0.0:${MANUGEN_API_PORT}"
echo "- API Documentation will be available at http://localhost:${MANUGEN_API_PORT}/docs"
echo "- Press Ctrl+C to stop the server"
echo ""
echo "(To run the server with a different port, set the MANUGEN_API_PORT environment variable.)"
echo ""

# Change to the backend directory
cd "$(dirname "$0")"

# ensure the text embedding model is downloaded
if [ "${USE_GEMINI_EMBEDDINGS:-0}" != "1" ]; then
    echo "* Downloading FlagEmbedding text embedding model (${FLAGEMBEDDING_MODEL_OR_PATH:-BAAI/bge-m3})..."
    uv run python -c "from manugen_ai.data import get_flag_embedding_model ; get_flag_embedding_model()"
else
    echo "* Using Gemini text embeddings via the Google GenAI API, skipping download."
fi

# Run the FastAPI server using uvicorn
if [ "HOT_RELOAD_BACKEND" = "1" ]; then
    # run in debug mode, with hot reloading
    exec uv run uvicorn src.main:app \
        --host 0.0.0.0 \
        --port ${MANUGEN_API_PORT} \
        --reload \
        --log-level info
else
    # run in production mode
    exec uv run uvicorn src.main:app \
        --host 0.0.0.0 \
        --port ${MANUGEN_API_PORT} \
        --workers ${WEB_CONCURRENCY:-8} \
        --log-level warning
fi
