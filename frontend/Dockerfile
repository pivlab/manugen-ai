# syntax=docker/dockerfile:1.7-labs

FROM oven/bun:latest

WORKDIR /app

# address issue with error within logs when running:
# `Error: Executable not found in $PATH: "xdg-open"`
RUN apt update && apt install xdg-utils --fix-missing -y

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY --exclude=node_modules . .

CMD ["bun", "run", "dev", "--host"]
