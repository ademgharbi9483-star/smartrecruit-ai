"""
SmartRecruit AI — Service de notifications.

Gère l'envoi de notifications :
  - Email aux candidats (confirmation de réception, changement de statut)
  - Webhook n8n pour orchestrer des workflows externes
  - Slack (optionnel) pour les alertes recruteurs
"""

import json
import logging
import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notify_cv_received(cv):
    """Envoie une confirmation de réception de CV au candidat."""
    subject = "CV reçu — SmartRecruit AI"
    message = (
        f"Bonjour {cv.candidate.get_full_name()},\n\n"
        f"Votre CV « {cv.original_name} » a bien été reçu et est en cours d'analyse.\n"
        f"Vous serez notifié(e) dès que l'analyse sera terminée.\n\n"
        f"L'équipe SmartRecruit AI"
    )
    _send_email(cv.candidate.email, subject, message)
    _trigger_n8n_webhook('cv_received', {
        'cv_id': cv.id,
        'candidate_email': cv.candidate.email,
        'candidate_name': cv.candidate.get_full_name(),
    })


def notify_cv_analyzed(cv):
    """Notifie le candidat que son CV a été analysé."""
    subject = "Analyse de votre CV terminée — SmartRecruit AI"
    num_skills = len(cv.extracted_data.get('skills', []))
    message = (
        f"Bonjour {cv.candidate.get_full_name()},\n\n"
        f"L'analyse de votre CV « {cv.original_name} » est terminée.\n"
        f"Nous avons détecté {num_skills} compétence(s).\n"
        f"Vous pouvez maintenant postuler aux offres d'emploi correspondant à votre profil.\n\n"
        f"L'équipe SmartRecruit AI"
    )
    _send_email(cv.candidate.email, subject, message)


def notify_application_received(application):
    """Confirme la réception d'une candidature."""
    subject = f"Candidature reçue — {application.job_offer.title}"
    message = (
        f"Bonjour {application.candidate.get_full_name()},\n\n"
        f"Votre candidature pour le poste « {application.job_offer.title} » "
        f"a bien été enregistrée.\n"
        f"Notre système IA va analyser votre profil et calculer un score de compatibilité.\n"
        f"Vous recevrez une notification à chaque mise à jour de votre candidature.\n\n"
        f"L'équipe SmartRecruit AI"
    )
    _send_email(application.candidate.email, subject, message)
    _trigger_n8n_webhook('application_received', {
        'application_id': application.id,
        'candidate_email': application.candidate.email,
        'candidate_name': application.candidate.get_full_name(),
        'job_title': application.job_offer.title,
        'recruiter_email': application.job_offer.recruiter.email,
    })


def notify_candidate_status_change(application, old_status, new_status):
    """Notifie le candidat d'un changement de statut de sa candidature."""
    status_labels = dict(application.Status.choices)
    old_label = status_labels.get(old_status, old_status)
    new_label = status_labels.get(new_status, new_status)

    subject = f"Mise à jour de votre candidature — {application.job_offer.title}"
    message = (
        f"Bonjour {application.candidate.get_full_name()},\n\n"
        f"Le statut de votre candidature pour le poste « {application.job_offer.title} » "
        f"a été mis à jour :\n"
        f"  Ancien statut : {old_label}\n"
        f"  Nouveau statut : {new_label}\n\n"
        f"Connectez-vous à votre espace candidat pour plus de détails.\n\n"
        f"L'équipe SmartRecruit AI"
    )
    _send_email(application.candidate.email, subject, message)


def notify_recruiter_new_application(application):
    """Alerte le recruteur d'une nouvelle candidature sur son offre."""
    recruiter = application.job_offer.recruiter
    subject = f"Nouvelle candidature — {application.job_offer.title}"
    message = (
        f"Bonjour {recruiter.get_full_name()},\n\n"
        f"Une nouvelle candidature a été soumise pour le poste "
        f"« {application.job_offer.title} ».\n"
        f"Candidat : {application.candidate.get_full_name()}\n"
        f"Le score de compatibilité sera disponible après l'analyse IA.\n\n"
        f"Consultez votre tableau de bord pour voir le classement des candidats.\n\n"
        f"SmartRecruit AI"
    )
    _send_email(recruiter.email, subject, message)
    _send_slack_alert(recruiter.get_full_name(), application)


# ── Helpers internes ────────────────────────────────────────────────────────────

def _send_email(to_email, subject, message):
    """Envoie un email de manière non-bloquante."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=True,
        )
        logger.info(f"Email envoyé à {to_email}: {subject}")
    except Exception as exc:
        logger.warning(f"Échec envoi email à {to_email}: {exc}")


def _trigger_n8n_webhook(event_type, payload):
    """Déclenche un webhook n8n pour orchestrer un workflow."""
    webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', None)
    if not webhook_url:
        return

    try:
        data = {'event': event_type, **payload}
        response = requests.post(
            f"{webhook_url}/{event_type}",
            json=data,
            timeout=5,
        )
        logger.info(f"Webhook n8n ({event_type}) — statut {response.status_code}")
    except Exception as exc:
        logger.warning(f"Échec webhook n8n ({event_type}): {exc}")


def _send_slack_alert(recruiter_name, application):
    """Envoie une alerte Slack (optionnel)."""
    slack_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
    if not slack_url:
        return

    try:
        payload = {
            "text": (
                f":bell: Nouvelle candidature — *{application.job_offer.title}*\n"
                f"Candidat : {application.candidate.get_full_name()}\n"
                f"Recruteur : {recruiter_name}"
            )
        }
        requests.post(slack_url, json=payload, timeout=5)
    except Exception as exc:
        logger.warning(f"Échec Slack: {exc}")
