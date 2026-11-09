"""
SmartRecruit AI — Routes Candidatures et CV
"""

from django.urls import path
from .views import (
    MyCandidateProfileView,
    CVUploadView,
    CVListView,
    CVDetailView,
    CVReanalyzeView,
    ApplicationCreateView,
    MyApplicationsView,
    ApplicationDetailView,
    JobApplicationsView,
    ApplicationStatusUpdateView,
    recruiter_dashboard_view,
)

urlpatterns = [
    # ── Profil candidat ────────────────────────────────────────────────────────
    path('profile/',              MyCandidateProfileView.as_view(),    name='candidate-profile'),

    # ── CV ──────────────────────────────────────────────────────────────────────
    path('cvs/',                  CVListView.as_view(),                 name='cv-list'),
    path('cvs/upload/',           CVUploadView.as_view(),               name='cv-upload'),
    path('cvs/<int:pk>/',         CVDetailView.as_view(),               name='cv-detail'),
    path('cvs/<int:pk>/reanalyze/',CVReanalyzeView.as_view(),          name='cv-reanalyze'),

    # ── Candidatures (candidat) ─────────────────────────────────────────────────
    path('applications/',         ApplicationCreateView.as_view(),       name='application-create'),
    path('applications/mine/',   MyApplicationsView.as_view(),           name='application-list-mine'),
    path('applications/<int:pk>/',ApplicationDetailView.as_view(),       name='application-detail'),

    # ── Candidatures (recruteur) ────────────────────────────────────────────────
    path('jobs/<int:job_id>/applications/', JobApplicationsView.as_view(), name='job-applications'),
    path('applications/<int:pk>/status/',   ApplicationStatusUpdateView.as_view(), name='application-status'),

    # ── Tableau de bord ──────────────────────────────────────────────────────────
    path('dashboard/',            recruiter_dashboard_view,             name='recruiter-dashboard'),
]
