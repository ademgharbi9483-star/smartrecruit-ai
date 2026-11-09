"""
SmartRecruit AI — Pipeline d'orchestration de l'analyse IA.

Coordonne les différentes briques du moteur IA :
  1. Extraction de texte PDF
  2. Extraction d'entités NLP
  3. Calcul du score de compatibilité
  4. Génération du résumé
  5. Mise à jour des modèles en base
  6. Notifications
"""

import time
import logging
from django.conf import settings

from apps.candidates.models import CV, Application
from apps.ai_engine.models import AIProcessingLog
from .pdf_extractor import extract_text_from_pdf
from .nlp_extractor import extract_entities
from .scoring import compute_compatibility_score, rank_applications
from .summarizer import generate_profile_summary, generate_short_summary
from .notifications import (
    notify_cv_received,
    notify_cv_analyzed,
    notify_application_received,
    notify_recruiter_new_application,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYSE COMPLÈTE D'UN CV
# ═══════════════════════════════════════════════════════════════════════════════

def run_cv_analysis(cv_id: int) -> dict:
    """
    Pipeline complet d'analyse d'un CV :
    extraction texte → extraction entités → stockage.

    Args:
        cv_id: ID du modèle CV à analyser.

    Returns:
        Dict avec le statut et les données extraites.
    """
    log = AIProcessingLog.objects.create(
        task_type=AIProcessingLog.TaskType.CV_EXTRACTION,
        status=AIProcessingLog.Status.PENDING,
        input_ref=str(cv_id),
    )
    start_time = time.time()

    try:
        cv = CV.objects.get(pk=cv_id)
        cv.processing_status = CV.ProcessingStatus.PROCESSING
        cv.save(update_fields=['processing_status'])

        # ── Étape 1 : Extraction du texte ──────────────────────────────────────
        file_path = cv.file.path
        extracted_text = extract_text_from_pdf(file_path)

        if not extracted_text.strip():
            raise ValueError("Aucun texte n'a pu être extrait du PDF (image seule ou corrompu).")

        cv.extracted_text = extracted_text
        logger.info(f"CV {cv_id} — Texte extrait ({len(extracted_text)} caractères)")

        # ── Étape 2 : Extraction d'entités (NLP) ───────────────────────────────
        entities = extract_entities(extracted_text)
        cv.extracted_data = entities
        cv.processing_status = CV.ProcessingStatus.DONE
        cv.processing_error = ''
        cv.save()

        # ── Étape 3 : Notifications ──────────────────────────────────────────────
        try:
            notify_cv_analyzed(cv)
        except Exception as exc:
            logger.warning(f"Notification échouée pour CV {cv_id}: {exc}")

        duration_ms = int((time.time() - start_time) * 1000)
        log.status = AIProcessingLog.Status.SUCCESS
        log.duration_ms = duration_ms
        log.output_ref = str(cv_id)
        log.save()

        logger.info(f"CV {cv_id} analysé en {duration_ms}ms — {len(entities.get('skills', []))} compétences")
        return {
            'status': 'success',
            'cv_id': cv_id,
            'extracted_skills': entities.get('skills', []),
            'processing_time_ms': duration_ms,
        }

    except Exception as exc:
        logger.error(f"Erreur analyse CV {cv_id}: {exc}", exc_info=True)
        try:
            cv = CV.objects.get(pk=cv_id)
            cv.processing_status = CV.ProcessingStatus.FAILED
            cv.processing_error = str(exc)[:500]
            cv.save()
        except Exception:
            pass

        log.status = AIProcessingLog.Status.FAILURE
        log.error_message = str(exc)[:500]
        log.duration_ms = int((time.time() - start_time) * 1000)
        log.save()

        return {'status': 'error', 'cv_id': cv_id, 'error': str(exc)}


# ═══════════════════════════════════════════════════════════════════════════════
#  SCORING D'UNE CANDIDATURE
# ═══════════════════════════════════════════════════════════════════════════════

def run_application_scoring(application_id: int) -> dict:
    """
    Pipeline complet de scoring d'une candidature :
    récupération CV + offre → calcul du score → résumé → classement.

    Args:
        application_id: ID du modèle Application à scorer.

    Returns:
        Dict avec le statut et le score calculé.
    """
    log = AIProcessingLog.objects.create(
        task_type=AIProcessingLog.TaskType.SCORING,
        status=AIProcessingLog.Status.PENDING,
        input_ref=str(application_id),
    )
    start_time = time.time()

    try:
        application = Application.objects.select_related(
            'candidate', 'job_offer', 'cv'
        ).get(pk=application_id)

        # ── Préparation des données ──────────────────────────────────────────────
        cv = application.cv
        cv_data = cv.extracted_data if cv and cv.extracted_data else {}

        # S'assurer que le CV a été analysé
        if cv and not cv_data:
            logger.info(f"CV {cv.id} non analysé — lancement de l'analyse...")
            run_cv_analysis(cv.id)
            cv.refresh_from_db()
            cv_data = cv.extracted_data

        job_offer_data = {
            'required_skills':   application.job_offer.required_skills,
            'experience_level':  application.job_offer.experience_level,
            'title':             application.job_offer.title,
            'description':       application.job_offer.description,
        }

        # ── Calcul du score ──────────────────────────────────────────────────────
        score_data = compute_compatibility_score(cv_data, job_offer_data)

        # ── Génération du résumé ───────────────────────────────────────────────
        full_summary = generate_profile_summary(cv_data, job_offer_data, score_data)
        short_summary = generate_short_summary(cv_data, score_data)

        # ── Mise à jour de la candidature ──────────────────────────────────────
        application.compatibility_score = score_data['global_score']
        application.score_details = score_data
        application.ai_summary = full_summary
        application.status = Application.Status.ANALYZING
        application.save()

        # ── Notification recruteur ──────────────────────────────────────────────
        try:
            notify_recruiter_new_application(application)
        except Exception as exc:
            logger.warning(f"Notification recruteur échouée: {exc}")

        duration_ms = int((time.time() - start_time) * 1000)
        log.status = AIProcessingLog.Status.SUCCESS
        log.duration_ms = duration_ms
        log.output_ref = str(application_id)
        log.save()

        logger.info(
            f"Candidature {application_id} scorée à {score_data['global_score']}/100 "
            f"en {duration_ms}ms (méthode: {score_data['method']})"
        )

        return {
            'status': 'success',
            'application_id': application_id,
            'score': score_data['global_score'],
            'matched_skills': score_data['matched_skills'],
            'missing_skills': score_data['missing_skills'],
            'processing_time_ms': duration_ms,
        }

    except Exception as exc:
        logger.error(f"Erreur scoring candidature {application_id}: {exc}", exc_info=True)

        log.status = AIProcessingLog.Status.FAILURE
        log.error_message = str(exc)[:500]
        log.duration_ms = int((time.time() - start_time) * 1000)
        log.save()

        return {'status': 'error', 'application_id': application_id, 'error': str(exc)}


# ═══════════════════════════════════════════════════════════════════════════════
#  CLASSEMENT DES CANDIDATURES POUR UNE OFFRE
# ═══════════════════════════════════════════════════════════════════════════════

def rerank_job_applications(job_offer_id: int) -> dict:
    """
    Recalcule et reclasse toutes les candidatures d'une offre.

    Args:
        job_offer_id: ID de l'offre d'emploi.

    Returns:
        Dict avec le nombre de candidatures classées.
    """
    applications = list(
        Application.objects.filter(
            job_offer_id=job_offer_id,
            compatibility_score__isnull=False,
        ).values('id', 'compatibility_score', 'candidate__first_name', 'candidate__last_name')
    )

    ranked = rank_applications(applications)

    logger.info(f"Offre {job_offer_id} — {len(ranked)} candidatures classées")
    return {'job_offer_id': job_offer_id, 'ranked_count': len(ranked), 'ranking': ranked}
