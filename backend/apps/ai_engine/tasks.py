"""
SmartRecruit AI — Tâches Celery asynchrones.

Les tâches IA lourdes (extraction, scoring) sont exécutées
de manière asynchrone pour ne pas bloquer l'interface utilisateur.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def analyze_cv_task(self, cv_id: int):
    """
    Tâche asynchrone : analyse complète d'un CV (extraction NLP).
    """
    try:
        from apps.ai_engine.services.pipeline import run_cv_analysis
        result = run_cv_analysis(cv_id)
        logger.info(f"Tâche analyze_cv_task terminée — CV {cv_id}: {result['status']}")
        return result
    except Exception as exc:
        logger.error(f"Tâche analyze_cv_task échouée — CV {cv_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def score_application_task(self, application_id: int):
    """
    Tâche asynchrone : calcul du score de compatibilité d'une candidature.
    """
    try:
        from apps.ai_engine.services.pipeline import run_application_scoring
        result = run_application_scoring(application_id)
        logger.info(
            f"Tâche score_application_task terminée — "
            f"Application {application_id}: score={result.get('score', 'N/A')}"
        )
        return result
    except Exception as exc:
        logger.error(f"Tâche score_application_task échouée — Application {application_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True)
def rerank_job_applications_task(self, job_offer_id: int):
    """
    Tâche asynchrone : reclassement des candidatures d'une offre.
    """
    try:
        from apps.ai_engine.services.pipeline import rerank_job_applications
        result = rerank_job_applications(job_offer_id)
        logger.info(f"Tâche rerank — Offre {job_offer_id}: {result['ranked_count']} candidatures")
        return result
    except Exception as exc:
        logger.error(f"Tâche rerank échouée — Offre {job_offer_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True)
def auto_close_expired_offers_task(self):
    """
    Tâche périodique : clôture automatique des offres expirées.
    À programmer avec Celery Beat (ex: toutes les heures).
    """
    from django.utils import timezone
    from apps.jobs.models import JobOffer

    expired = JobOffer.objects.filter(
        status=JobOffer.Status.ACTIVE,
        expires_at__lt=timezone.now(),
    )
    count = expired.count()
    for offer in expired:
        offer.auto_close_if_expired()

    logger.info(f"Tâche auto_close — {count} offre(s) clôturée(s) automatiquement")
    return {'closed_count': count}
