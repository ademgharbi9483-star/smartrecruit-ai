# ── SmartRecruit AI — Backend Dockerfile ────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gcc \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/media /app/static

# Rendre tous les entrypoints exécutables
RUN chmod +x /app/entrypoint.sh /app/entrypoint-celery.sh /app/entrypoint-beat.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
