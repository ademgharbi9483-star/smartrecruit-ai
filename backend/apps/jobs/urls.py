"""
SmartRecruit AI — Routes Offres d'emploi
"""

from django.urls import path
from .views import (
    JobOfferListView,
    JobOfferDetailView,
    JobOfferCreateView,
    JobOfferUpdateView,
    JobOfferDeleteView,
    RecruiterJobOffersView,
    JobOfferCloseView,
    job_stats_view,
)

urlpatterns = [
    # ── Lecture publique ────────────────────────────────────────────────────────
    path('',                    JobOfferListView.as_view(),       name='job-list'),
    path('stats/',              job_stats_view,                   name='job-stats'),
    path('<int:pk>/',           JobOfferDetailView.as_view(),     name='job-detail'),

    # ── Actions recruteur ───────────────────────────────────────────────────────
    path('create/',             JobOfferCreateView.as_view(),     name='job-create'),
    path('my-offers/',          RecruiterJobOffersView.as_view(), name='job-my-offers'),
    path('<int:pk>/update/',    JobOfferUpdateView.as_view(),     name='job-update'),
    path('<int:pk>/delete/',    JobOfferDeleteView.as_view(),     name='job-delete'),
    path('<int:pk>/close/',     JobOfferCloseView.as_view(),      name='job-close'),
]
