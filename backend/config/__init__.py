"""
SmartRecruit AI — Package de configuration Django.
Importe l'application Celery pour la découverte des tâches.
"""

from .celery import app as celery_app

__all__ = ('celery_app',)
