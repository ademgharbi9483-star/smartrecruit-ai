"""
SmartRecruit AI — Admin Offres d'emploi
"""

from django.contrib import admin
from .models import JobOffer


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display  = ['title', 'recruiter', 'contract_type', 'location', 'status', 'created_at']
    list_filter   = ['status', 'contract_type', 'experience_level']
    search_fields = ['title', 'description', 'location', 'sector']
    ordering      = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'description', 'recruiter', 'status')
        }),
        ('Détails du poste', {
            'fields': ('location', 'contract_type', 'experience_level', 'sector',
                       'salary_min', 'salary_max', 'required_skills')
        }),
        ('Dates', {
            'fields': ('expires_at', 'created_at', 'updated_at')
        }),
    )
