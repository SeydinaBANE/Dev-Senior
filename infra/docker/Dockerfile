# Stage 1: Frontend build
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json .
RUN npm ci
COPY frontend/ .
ARG VITE_BASE_PATH=/app/
ARG VITE_API_KEY=
ENV VITE_BASE_PATH=${VITE_BASE_PATH}
ENV VITE_API_KEY=${VITE_API_KEY}
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --gid 1001 --no-create-home --shell /sbin/nologin app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY agents/ agents/
COPY api/ api/
COPY memory/ memory/
COPY mcp_servers/ mcp_servers/
COPY observability/ observability/
COPY --from=frontend /build/dist frontend/dist/

RUN pip install --no-cache-dir . && rm -rf /root/.cache/pip

RUN chown -R app:app /app
USER app

EXPOSE 8080

ENV PORT=8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:${PORT:-8080}/dev-senior/health || exit 1

CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --workers 2
