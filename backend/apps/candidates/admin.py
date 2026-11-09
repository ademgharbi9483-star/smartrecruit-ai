from django.contrib import admin
from .models import CV, Application, CandidateProfile


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'headline', 'location', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'headline']


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display  = ['candidate', 'original_name', 'processing_status', 'is_primary', 'created_at']
    list_filter   = ['processing_status', 'is_primary']
    search_fields = ['candidate__email', 'original_name']
    readonly_fields = ['created_at', 'updated_at', 'extracted_text', 'extracted_data']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display  = ['candidate', 'job_offer', 'status', 'compatibility_score', 'applied_at']
    list_filter   = ['status']
    search_fields = ['candidate__email', 'job_offer__title']
    ordering      = ['-compatibility_score']
    readonly_fields = ['applied_at', 'updated_at', 'compatibility_score', 'score_details', 'ai_summary']
