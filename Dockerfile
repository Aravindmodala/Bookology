# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

ENV POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app \
    && apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

USER app

EXPOSE 8000

# Set async event loop policy for better performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONASYNCIODEBUG=0 \
    UVICORN_WORKERS=4 \
    UVICORN_WORKER_CLASS=uvicorn.workers.UvicornWorker \
    UVICORN_WORKER_CONNECTIONS=1000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/healthz | grep -q 'ok' || exit 1

# Optimized for concurrency: 4 workers, async worker class, high connection limit
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--limit-concurrency", "1000", "--timeout-keep-alive", "5"]


