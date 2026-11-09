#!/bin/sh
set -e

echo "==> Running migrations (celery)..."
python manage.py migrate --noinput

echo "==> Starting Celery worker..."
exec celery -A config worker --loglevel=info --concurrency=2
