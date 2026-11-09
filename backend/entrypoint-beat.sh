#!/bin/sh
set -e

echo "==> Running migrations (beat)..."
python manage.py migrate --noinput

echo "==> Starting Celery Beat..."
exec celery -A config beat --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
