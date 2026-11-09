"""
SmartRecruit AI — Routes Moteur IA
"""

from django.urls import path
from .views import (
    chatbot_view,
    analyze_cv_view,
    cv_analysis_result_view,
    ai_dashboard_view,
    rerank_applications_view,
)

urlpatterns = [
    # ── Chatbot RH ──────────────────────────────────────────────────────────────
    path('chatbot/',                        chatbot_view,               name='ai-chatbot'),

    # ── Analyse CV ──────────────────────────────────────────────────────────────
    path('analyze-cv/<int:cv_id>/',         analyze_cv_view,            name='ai-analyze-cv'),
    path('cv/<int:cv_id>/result/',          cv_analysis_result_view,    name='ai-cv-result'),

    # ── Tableau de bord IA ──────────────────────────────────────────────────────
    path('dashboard/',                      ai_dashboard_view,          name='ai-dashboard'),

    # ── Reclassement ────────────────────────────────────────────────────────────
    path('rerank/<int:job_id>/',            rerank_applications_view,   name='ai-rerank'),
]
