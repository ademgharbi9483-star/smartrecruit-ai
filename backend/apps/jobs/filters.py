"""
SmartRecruit AI — Filtres pour les offres d'emploi
"""

import django_filters
from .models import JobOffer


class JobOfferFilter(django_filters.FilterSet):
    """Filtres avancés pour la recherche d'offres d'emploi."""

    title           = django_filters.CharFilter(lookup_expr='icontains', label="Titre")
    location        = django_filters.CharFilter(lookup_expr='icontains', label="Localisation")
    sector          = django_filters.CharFilter(lookup_expr='icontains', label="Secteur")
    contract_type   = django_filters.ChoiceFilter(
        choices=JobOffer.ContractType.choices, label="Type de contrat"
    )
    experience_level = django_filters.ChoiceFilter(
        choices=JobOffer.ExperienceLevel.choices, label="Niveau d'expérience"
    )
    status          = django_filters.ChoiceFilter(
        choices=JobOffer.Status.choices, label="Statut"
    )
    salary_min      = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max      = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    created_after   = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before  = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model  = JobOffer
        fields = [
            'title', 'location', 'sector',
            'contract_type', 'experience_level', 'status',
            'salary_min', 'salary_max',
            'created_after', 'created_before',
        ]
