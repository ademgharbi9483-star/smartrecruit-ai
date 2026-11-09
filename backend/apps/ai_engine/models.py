"""
SmartRecruit AI — Modèles moteur IA (logs et historique)
"""

from django.db import models


class AIProcessingLog(models.Model):
    """Journal des traitements IA pour suivi et audit."""

    class TaskType(models.TextChoices):
        CV_EXTRACTION = 'cv_extraction', 'Extraction CV'
        SCORING       = 'scoring',       'Calcul score'
        SUMMARY       = 'summary',       'Génération résumé'
        CHATBOT       = 'chatbot',       'Chatbot RH'

    class Status(models.TextChoices):
        SUCCESS = 'success', 'Succès'
        FAILURE = 'failure', 'Échec'
        PENDING = 'pending', 'En cours'

    task_type       = models.CharField(max_length=30, choices=TaskType.choices)
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    input_ref       = models.CharField(max_length=255, blank=True, help_text="ID de l'objet en entrée")
    output_ref      = models.CharField(max_length=255, blank=True, help_text="ID de l'objet en sortie")
    duration_ms     = models.PositiveIntegerField(null=True, blank=True, verbose_name="Durée (ms)")
    error_message   = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'ai_processing_logs'
        ordering  = ['-created_at']
        verbose_name        = 'Log IA'
        verbose_name_plural = 'Logs IA'

    def __str__(self):
        return f"[{self.task_type}] {self.status} — {self.created_at:%Y-%m-%d %H:%M}"
