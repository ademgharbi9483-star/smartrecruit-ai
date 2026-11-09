from django.contrib import admin
from .models import AIProcessingLog


@admin.register(AIProcessingLog)
class AIProcessingLogAdmin(admin.ModelAdmin):
    list_display  = ['task_type', 'status', 'input_ref', 'duration_ms', 'created_at']
    list_filter   = ['task_type', 'status']
    readonly_fields = ['created_at']
