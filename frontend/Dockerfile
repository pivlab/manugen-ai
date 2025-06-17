# syntax=docker/dockerfile:1.7-labs

FROM oven/bun:latest

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY --exclude=node_modules . .

CMD ["bun", "run", "dev", "--host"]
