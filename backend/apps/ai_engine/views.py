"""
SmartRecruit AI — Vues Moteur IA
"""

import logging
from django.db.models import Avg, Count, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.authentication.permissions import IsCandidat, IsRecruteurOrAdmin
from apps.candidates.models import CV, Application
from apps.jobs.models import JobOffer
from .models import AIProcessingLog
from .serializers import (
    ChatbotMessageSerializer,
    DashboardStatsSerializer,
)
from .services.chatbot import get_chatbot_response
from .services.pipeline import run_cv_analysis, run_application_scoring

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#  CHATBOT RH
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chatbot_view(request):
    """
    POST /api/v1/ai/chatbot/
    Chatbot RH — répond aux questions fréquentes des candidats.

    Body: {"message": "...", "conversation_id": "..."}
    """
    serializer = ChatbotMessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    message = serializer.validated_data['message']

    # Contexte utilisateur pour personnaliser les réponses
    user_context = {}
    if request.user.is_candidat:
        apps = Application.objects.filter(
            candidate=request.user
        ).select_related('job_offer').order_by('-applied_at')[:5]
        user_context['applications'] = [
            {
                'job_title': app.job_offer.title,
                'status': app.status,
                'status_display': app.get_status_display(),
                'compatibility_score': app.compatibility_score,
            }
            for app in apps
        ]

    result = get_chatbot_response(message, user_context)

    # Si escalade nécessaire, logger la demande
    if result.get('needs_escalation'):
        AIProcessingLog.objects.create(
            task_type=AIProcessingLog.TaskType.CHATBOT,
            status=AIProcessingLog.Status.FAILURE,
            input_ref=f"user:{request.user.id}",
            error_message=f"Escalade requise pour: {message[:200]}",
        )
    else:
        AIProcessingLog.objects.create(
            task_type=AIProcessingLog.TaskType.CHATBOT,
            status=AIProcessingLog.Status.SUCCESS,
            input_ref=f"user:{request.user.id}",
            output_ref=result.get('matched_question', ''),
            duration_ms=int(result.get('confidence', 0) * 1000),
        )

    return Response(result, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYSE IA — ENDPOINTS SYNCHRONES
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCandidat])
def analyze_cv_view(request, cv_id):
    """
    POST /api/v1/ai/analyze-cv/<cv_id>/
    Lance l'analyse IA d'un CV (synchrone ou asynchrone).
    """
    try:
        cv = CV.objects.get(pk=cv_id, candidate=request.user)
    except CV.DoesNotExist:
        return Response({"error": "CV introuvable."}, status=status.HTTP_404_NOT_FOUND)

    # Tenter asynchrone d'abord
    try:
        from .tasks import analyze_cv_task
        analyze_cv_task.delay(cv.id)
        return Response(
            {"message": "Analyse lancée en arrière-plan.", "cv_id": cv.id},
            status=status.HTTP_202_ACCEPTED,
        )
    except Exception:
        # Fallback synchrone
        result = run_cv_analysis(cv.id)
        if result['status'] == 'success':
            cv.refresh_from_db()
            return Response(
                {
                    "message": "Analyse terminée.",
                    "cv_id": cv.id,
                    "extracted_skills": cv.extracted_data.get('skills', []),
                    "processing_status": cv.processing_status,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": result.get('error', 'Échec de l\'analyse')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cv_analysis_result_view(request, cv_id):
    """
    GET /api/v1/ai/cv/<cv_id>/result/
    Récupère le résultat de l'analyse IA d'un CV.
    """
    try:
        if request.user.is_candidat:
            cv = CV.objects.get(pk=cv_id, candidate=request.user)
        elif request.user.is_recruteur or request.user.is_admin:
            cv = CV.objects.get(pk=cv_id)
        else:
            return Response({"error": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
    except CV.DoesNotExist:
        return Response({"error": "CV introuvable."}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "cv_id": cv.id,
        "processing_status": cv.processing_status,
        "processing_error": cv.processing_error,
        "extracted_data": cv.extracted_data,
        "skills": cv.extracted_data.get('skills', []),
        "summary": cv.extracted_data.get('summary', ''),
    }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════════
#  TABLEAU DE BORD IA — STATISTIQUES GLOBALES
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsRecruteurOrAdmin])
def ai_dashboard_view(request):
    """
    GET /api/v1/ai/dashboard/
    Statistiques globales du moteur IA (admin/recruteur).
    """
    total_cvs = CV.objects.count()
    analyzed_cvs = CV.objects.filter(processing_status=CV.ProcessingStatus.DONE).count()
    total_apps = Application.objects.count()
    scored_apps = Application.objects.filter(compatibility_score__isnull=False).count()
    avg_score = Application.objects.filter(
        compatibility_score__isnull=False
    ).aggregate(avg=Avg('compatibility_score'))['avg'] or 0

    by_status = {}
    for s_code, s_label in CV.ProcessingStatus.choices:
        by_status[s_code] = {
            'label': s_label,
            'count': CV.objects.filter(processing_status=s_code).count(),
        }

    ai_logs = AIProcessingLog.objects.count()
    ai_logs_success = AIProcessingLog.objects.filter(
        status=AIProcessingLog.Status.SUCCESS
    ).count()
    ai_logs_failure = AIProcessingLog.objects.filter(
        status=AIProcessingLog.Status.FAILURE
    ).count()

    # Logs récents
    recent_logs = AIProcessingLog.objects.all()[:10]
    logs_data = [
        {
            'task_type': log.get_task_type_display(),
            'status': log.status,
            'duration_ms': log.duration_ms,
            'created_at': log.created_at.isoformat(),
        }
        for log in recent_logs
    ]

    return Response({
        'total_cvs': total_cvs,
        'analyzed_cvs': analyzed_cvs,
        'total_applications': total_apps,
        'scored_applications': scored_apps,
        'avg_score': round(avg_score, 2),
        'by_processing_status': by_status,
        'ai_logs_count': ai_logs,
        'ai_logs_success': ai_logs_success,
        'ai_logs_failure': ai_logs_failure,
        'recent_logs': logs_data,
    }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════════
#  RERANK — RECLASSEMENT DES CANDIDATURES
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsRecruteurOrAdmin])
def rerank_applications_view(request, job_id):
    """
    POST /api/v1/ai/rerank/<job_id>/
    Reclasse les candidatures d'une offre par score.
    """
    try:
        job = JobOffer.objects.get(pk=job_id)
    except JobOffer.DoesNotExist:
        return Response({"error": "Offre introuvable."}, status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_admin and job.recruiter != request.user:
        return Response({"error": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

    from .services.pipeline import rerank_job_applications
    result = rerank_job_applications(job_id)
    return Response(result, status=status.HTTP_200_OK)
