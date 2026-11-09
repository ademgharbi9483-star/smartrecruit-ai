"""
SmartRecruit AI — Sérialiseurs Moteur IA
"""

from rest_framework import serializers


class ChatbotMessageSerializer(serializers.Serializer):
    """Requête du chatbot RH."""
    message = serializers.CharField(
        max_length=1000,
        required=True,
        help_text="Question du candidat"
    )
    conversation_id = serializers.CharField(
        max_length=100, required=False, allow_blank=True,
        help_text="ID de conversation pour le contexte"
    )


class ChatbotResponseSerializer(serializers.Serializer):
    """Réponse du chatbot RH."""
    answer = serializers.CharField()
    matched_question = serializers.CharField(allow_null=True)
    confidence = serializers.FloatField()
    needs_escalation = serializers.BooleanField()


class CVAnalysisResultSerializer(serializers.Serializer):
    """Résultat de l'analyse d'un CV."""
    cv_id = serializers.IntegerField()
    status = serializers.CharField()
    extracted_skills = serializers.ListField(child=serializers.CharField())
    processing_time_ms = serializers.IntegerField(required=False)
    error = serializers.CharField(required=False)


class ScoringResultSerializer(serializers.Serializer):
    """Résultat du scoring d'une candidature."""
    application_id = serializers.IntegerField()
    status = serializers.CharField()
    score = serializers.FloatField(required=False)
    matched_skills = serializers.ListField(child=serializers.CharField(), required=False)
    missing_skills = serializers.ListField(child=serializers.CharField(), required=False)
    processing_time_ms = serializers.IntegerField(required=False)
    error = serializers.CharField(required=False)


class DashboardStatsSerializer(serializers.Serializer):
    """Statistiques globales du tableau de bord."""
    total_cvs = serializers.IntegerField()
    analyzed_cvs = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    scored_applications = serializers.IntegerField()
    avg_score = serializers.FloatField()
    by_processing_status = serializers.DictField()
    ai_logs_count = serializers.IntegerField()
