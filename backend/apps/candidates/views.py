"""
SmartRecruit AI — Vues Candidatures et CV
"""

from django.utils import timezone
from django.db.models import Q, Count, Avg
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend

from apps.authentication.permissions import IsCandidat, IsRecruteurOrAdmin
from apps.jobs.models import JobOffer
from .models import CandidateProfile, CV, Application
from .serializers import (
    CandidateProfileSerializer,
    CVSerializer,
    CVUploadSerializer,
    ApplicationSerializer,
    ApplicationCreateSerializer,
    ApplicationStatusUpdateSerializer,
    RankedApplicationSerializer,
)


# ═════════════════════════════════════════════════════════════════════════════════
#  GESTION DU PROFIL CANDIDAT
# ═════════════════════════════════════════════════════════════════════════════════

class MyCandidateProfileView(generics.RetrieveUpdateAPIView):
    """
    GET    /api/v1/candidates/profile/   — Consulter mon profil candidat
    PUT    /api/v1/candidates/profile/   — Mettre à jour mon profil
    PATCH  /api/v1/candidates/profile/   — Mise à jour partielle
    """
    serializer_class   = CandidateProfileSerializer
    permission_classes = [IsAuthenticated, IsCandidat]

    def get_object(self):
        profile, _ = CandidateProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'headline': '', 'summary': '', 'location': self.request.user.phone},
        )
        return profile


# ═════════════════════════════════════════════════════════════════════════════════
#  GESTION DES CV
# ═════════════════════════════════════════════════════════════════════════════════

class CVUploadView(generics.CreateAPIView):
    """
    POST /api/v1/candidates/cvs/upload/
    Upload d'un CV au format PDF. Déclenche l'analyse IA en arrière-plan.
    """
    serializer_class   = CVUploadSerializer
    permission_classes = [IsAuthenticated, IsCandidat]
    parser_classes     = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cv = serializer.save()

        # Déclenchement de l'analyse IA asynchrone (Celery)
        try:
            from apps.ai_engine.tasks import analyze_cv_task
            analyze_cv_task.delay(cv.id)
        except Exception:
            # Si Celery n'est pas disponible, on déclenche en synchrone
            try:
                from apps.ai_engine.services.pipeline import run_cv_analysis
                run_cv_analysis(cv.id)
            except Exception as exc:
                pass  # L'erreur est non-bloquante ; l'utilisateur pourra relancer

        return Response(
            CVSerializer(cv).data,
            status=status.HTTP_201_CREATED,
        )


class CVListView(generics.ListAPIView):
    """
    GET /api/v1/candidates/cvs/
    Liste des CV du candidat connecté.
    """
    serializer_class   = CVSerializer
    permission_classes = [IsAuthenticated, IsCandidat]

    def get_queryset(self):
        return CV.objects.filter(candidate=self.request.user)


class CVDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/v1/candidates/cvs/<id>/   — Détail d'un CV
    DELETE /api/v1/candidates/cvs/<id>/   — Suppression d'un CV
    """
    serializer_class   = CVSerializer
    permission_classes = [IsAuthenticated, IsCandidat]

    def get_queryset(self):
        return CV.objects.filter(candidate=self.request.user)


class CVReanalyzeView(APIView):
    """
    POST /api/v1/candidates/cvs/<id>/reanalyze/
    Relance l'analyse IA d'un CV.
    """
    permission_classes = [IsAuthenticated, IsCandidat]

    def post(self, request, pk):
        try:
            cv = CV.objects.get(pk=pk, candidate=request.user)
        except CV.DoesNotExist:
            return Response({"error": "CV introuvable."}, status=status.HTTP_404_NOT_FOUND)

        cv.processing_status = CV.ProcessingStatus.PENDING
        cv.save(update_fields=['processing_status'])

        try:
            from apps.ai_engine.tasks import analyze_cv_task
            analyze_cv_task.delay(cv.id)
        except Exception:
            from apps.ai_engine.services.pipeline import run_cv_analysis
            run_cv_analysis(cv.id)

        return Response(
            {"message": "Analyse relancée.", "cv_id": cv.id},
            status=status.HTTP_200_OK,
        )


# ═════════════════════════════════════════════════════════════════════════════════
#  GESTION DES CANDIDATURES
# ═════════════════════════════════════════════════════════════════════════════════

class ApplicationCreateView(generics.CreateAPIView):
    """
    POST /api/v1/candidates/applications/
    Soumission d'une candidature à une offre. Déclenche le calcul de score IA.
    """
    serializer_class   = ApplicationCreateSerializer
    permission_classes = [IsAuthenticated, IsCandidat]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        # Déclenchement du scoring IA
        try:
            from apps.ai_engine.tasks import score_application_task
            score_application_task.delay(application.id)
        except Exception:
            try:
                from apps.ai_engine.services.pipeline import run_application_scoring
                run_application_scoring(application.id)
            except Exception:
                pass

        return Response(
            ApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )


class MyApplicationsView(generics.ListAPIView):
    """
    GET /api/v1/candidates/applications/
    Liste des candidatures du candidat connecté.
    """
    serializer_class   = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsCandidat]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields     = ['applied_at', 'compatibility_score', 'status']
    ordering            = ['-applied_at']

    def get_queryset(self):
        return Application.objects.filter(
            candidate=self.request.user
        ).select_related('job_offer', 'cv')


class ApplicationDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/candidates/applications/<id>/
    Détail d'une candidature (candidat propriétaire ou recruteur/admin).
    """
    serializer_class   = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_candidat:
            return Application.objects.filter(candidate=user)
        return Application.objects.all()


# ═════════════════════════════════════════════════════════════════════════════════
#  VUES RECRUTEUR — CANDIDATURES PAR OFFRE
# ═════════════════════════════════════════════════════════════════════════════════

class JobApplicationsView(generics.ListAPIView):
    """
    GET /api/v1/candidates/jobs/<job_id>/applications/
    Liste classée des candidatures pour une offre (recruteurs/admin).
    Tri par score de compatibilité décroissant.
    """
    serializer_class   = RankedApplicationSerializer
    permission_classes = [IsAuthenticated, IsRecruteurOrAdmin]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields     = ['compatibility_score', 'applied_at', 'status']
    ordering            = ['-compatibility_score']

    def get_queryset(self):
        job_id = self.kwargs['job_id']
        try:
            job = JobOffer.objects.get(pk=job_id)
        except JobOffer.DoesNotExist:
            return Application.objects.none()

        # Le recruteur ne voit que ses offres (sauf admin)
        user = self.request.user
        if not user.is_admin and job.recruiter != user:
            return Application.objects.none()

        return Application.objects.filter(
            job_offer_id=job_id
        ).select_related('candidate', 'job_offer', 'cv')


class ApplicationStatusUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/v1/candidates/applications/<id>/status/
    Mise à jour du statut d'une candidature par un recruteur.
    """
    serializer_class   = ApplicationStatusUpdateSerializer
    permission_classes = [IsAuthenticated, IsRecruteurOrAdmin]
    http_method_names  = ['patch']

    def get_queryset(self):
        user = self.request.user
        qs = Application.objects.select_related('job_offer')
        if user.is_admin:
            return qs
        return qs.filter(job_offer__recruiter=user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_status = instance.status
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notification automatique au candidat (non-bloquante)
        new_status = serializer.validated_data.get('status', old_status)
        if new_status != old_status:
            try:
                from apps.ai_engine.services.notifications import notify_candidate_status_change
                notify_candidate_status_change(instance, old_status, new_status)
            except Exception:
                pass

        return Response(
            ApplicationSerializer(instance).data,
            status=status.HTTP_200_OK,
        )


# ═════════════════════════════════════════════════════════════════════════════════
#  TABLEAU DE BORD RECRUTEUR — STATISTIQUES
# ═════════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsRecruteurOrAdmin])
def recruiter_dashboard_view(request):
    """
    GET /api/v1/candidates/dashboard/
    Tableau de bord recruteur : statistiques globales et par offre.
    """
    user = request.user
    if user.is_admin:
        jobs_qs = JobOffer.objects.all()
        apps_qs = Application.objects.all()
    else:
        jobs_qs = JobOffer.objects.filter(recruiter=user)
        apps_qs = Application.objects.filter(job_offer__recruiter=user)

    # ── Statistiques globales ───────────────────────────────────────────────────
    total_jobs        = jobs_qs.count()
    active_jobs       = jobs_qs.filter(status='active').count()
    total_apps        = apps_qs.count()
    avg_score         = apps_qs.filter(
        compatibility_score__isnull=False
    ).aggregate(avg=Avg('compatibility_score'))['avg'] or 0

    # ── Répartition par statut ───────────────────────────────────────────────────
    by_status = {}
    for s_code, s_label in Application.Status.choices:
        by_status[s_code] = {
            'label': s_label,
            'count': apps_qs.filter(status=s_code).count(),
        }

    # ── Top candidatures (score le plus élevé) ───────────────────────────────────
    top_apps = apps_qs.filter(
        compatibility_score__isnull=False
    ).order_by('-compatibility_score')[:5]
    top_apps_data = RankedApplicationSerializer(top_apps, many=True).data

    # ── Candidatures par offre ───────────────────────────────────────────────────
    jobs_summary = []
    for job in jobs_qs.annotate(apps_count=Count('applications'))[:20]:
        job_apps = apps_qs.filter(job_offer=job)
        job_avg = job_apps.filter(
            compatibility_score__isnull=False
        ).aggregate(avg=Avg('compatibility_score'))['avg'] or 0
        jobs_summary.append({
            'job_id':         job.id,
            'title':          job.title,
            'status':         job.status,
            'applications':   job_apps.count(),
            'avg_score':      round(job_avg, 2),
        })

    return Response({
        'global': {
            'total_jobs':       total_jobs,
            'active_jobs':      active_jobs,
            'total_applications': total_apps,
            'avg_compatibility_score': round(avg_score, 2),
        },
        'by_status':    by_status,
        'top_applications': top_apps_data,
        'jobs_summary': jobs_summary,
    })
