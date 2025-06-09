# syntax=docker/dockerfile:1.7-labs 

# copied from https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers

# note that this Dockerfile's context should be set to the project root, due to
# the fact that it relies on a package under /packages/manugen-ai
# all backend-specific path refs should be prefixed with `backend/`

# Install uv
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# copy packages/manugen-ai into /opt/manugen-ai
COPY --exclude=.venv ./packages/manugen-ai /opt/manugen-ai

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    uv sync

# copy backend contents into working dir
COPY ./backend/ .

# for now, simply run the ADK test webserver
CMD ["/app/start_adk_web.sh"]
