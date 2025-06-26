# syntax=docker/dockerfile:1.7-labs

# copied from https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers

# note that this Dockerfile's context should be set to the project root, due to
# the fact that it relies on a package under /packages/manugen-ai
# all backend-specific path refs should be prefixed with `backend/`

# Install uv
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# install system dependencies, tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake build-essential pkg-config libgoogle-perftools-dev \
    zlib1g-dev curl

# Change the working directory to the `app` directory
WORKDIR /app

# copy packages/manugen-ai into /opt/manugen-ai
COPY --exclude=.venv ./packages/manugen-ai/ /packages/manugen-ai/

# Install dependencies
ENV VIRTUAL_ENV=/app/.venv
ENV UV_LINK_MODE=copy
ENV UV_NO_SYNC=1
COPY ./backend/pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --cache-dir /root/.cache/uv

# copy backend contents into working dir
COPY --exclude=.venv ./backend/ .

# for now, simply run the ADK test webserver
CMD ["/app/start_api_server.sh"]
