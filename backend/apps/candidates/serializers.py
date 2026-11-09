"""
SmartRecruit AI — Sérialiseurs Candidatures et CV
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import CandidateProfile, CV, Application

User = get_user_model()


# ── Profil candidat ─────────────────────────────────────────────────────────────

class CandidateProfileSerializer(serializers.ModelSerializer):
    """Profil étendu d'un candidat."""

    full_name  = serializers.SerializerMethodField(read_only=True)
    email      = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = CandidateProfile
        fields = [
            'id', 'user', 'full_name', 'email',
            'headline', 'summary', 'linkedin_url',
            'github_url', 'portfolio_url', 'location',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'full_name', 'email', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_email(self, obj):
        return obj.user.email


# ── CV ──────────────────────────────────────────────────────────────────────────

class CVSerializer(serializers.ModelSerializer):
    """CV uploadé par un candidat."""

    candidate_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = CV
        fields = [
            'id', 'candidate', 'candidate_name',
            'original_name', 'file_size', 'is_primary',
            'processing_status', 'processing_error',
            'extracted_data',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'candidate', 'candidate_name', 'original_name',
            'file_size', 'processing_status', 'processing_error',
            'extracted_data', 'created_at', 'updated_at',
        ]

    def get_candidate_name(self, obj):
        return obj.candidate.get_full_name()


class CVUploadSerializer(serializers.ModelSerializer):
    """Sérialiseur pour l'upload de CV (champ fichier uniquement)."""

    class Meta:
        model  = CV
        fields = ['file', 'is_primary']

    def validate_file(self, value):
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext != '.pdf':
            raise serializers.ValidationError("Seuls les fichiers PDF sont acceptés.")
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10 Mo.")
        return value

    def create(self, validated_data):
        request = self.context['request']
        file = validated_data['file']
        cv = CV.objects.create(
            candidate=request.user,
            file=file,
            original_name=file.name,
            file_size=file.size,
            is_primary=validated_data.get('is_primary', False),
        )
        return cv


# ── Candidature ──────────────────────────────────────────────────────────────────

class ApplicationSerializer(serializers.ModelSerializer):
    """Sérialiseur complet d'une candidature (vue recruteur)."""

    candidate_name     = serializers.SerializerMethodField(read_only=True)
    candidate_email    = serializers.SerializerMethodField(read_only=True)
    candidate_avatar    = serializers.SerializerMethodField(read_only=True)
    job_title          = serializers.SerializerMethodField(read_only=True)
    job_location       = serializers.SerializerMethodField(read_only=True)
    cv_original_name   = serializers.SerializerMethodField(read_only=True)
    status_display     = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Application
        fields = [
            'id', 'candidate', 'candidate_name', 'candidate_email', 'candidate_avatar',
            'job_offer', 'job_title', 'job_location',
            'cv', 'cv_original_name',
            'status', 'status_display',
            'cover_letter',
            'compatibility_score', 'score_details', 'ai_summary',
            'recruiter_notes',
            'applied_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'candidate', 'candidate_name', 'candidate_email', 'candidate_avatar',
            'job_title', 'job_location', 'cv_original_name',
            'status_display', 'compatibility_score', 'score_details', 'ai_summary',
            'applied_at', 'updated_at',
        ]

    def get_candidate_name(self, obj):
        return obj.candidate.get_full_name()

    def get_candidate_email(self, obj):
        return obj.candidate.email

    def get_candidate_avatar(self, obj):
        return obj.candidate.avatar.url if obj.candidate.avatar else None

    def get_job_title(self, obj):
        return obj.job_offer.title

    def get_job_location(self, obj):
        return obj.job_offer.location

    def get_cv_original_name(self, obj):
        return obj.cv.original_name if obj.cv else None

    def get_status_display(self, obj):
        return obj.get_status_display()


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la soumission d'une candidature par un candidat."""

    class Meta:
        model  = Application
        fields = ['job_offer', 'cv', 'cover_letter']

    def validate(self, attrs):
        request = self.context['request']
        job_offer = attrs['job_offer']
        cv = attrs.get('cv')

        # L'offre doit être active
        if job_offer.status != 'active':
            raise serializers.ValidationError(
                {"job_offer": "Cette offre n'est plus ouverte aux candidatures."}
            )

        # Le CV doit appartenir au candidat
        if cv and cv.candidate != request.user:
            raise serializers.ValidationError(
                {"cv": "Ce CV ne vous appartient pas."}
            )

        # Vérifier unicité de la candidature
        existing = Application.objects.filter(
            candidate=request.user, job_offer=job_offer
        ).exists()
        if existing:
            raise serializers.ValidationError(
                {"job_offer": "Vous avez déjà postulé à cette offre."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        application = Application.objects.create(
            candidate=request.user,
            **validated_data,
        )
        return application


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la mise à jour du statut par un recruteur."""

    class Meta:
        model  = Application
        fields = ['status', 'recruiter_notes']

    def validate_status(self, value):
        valid = [s[0] for s in Application.Status.choices]
        if value not in valid:
            raise serializers.ValidationError("Statut invalide.")
        return value


class RankedApplicationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur allégé pour le classement des candidats par score.
    Utilisé par le tableau de bord recruteur.
    """

    candidate_name = serializers.SerializerMethodField(read_only=True)
    candidate_email = serializers.SerializerMethodField(read_only=True)
    job_title      = serializers.SerializerMethodField(read_only=True)
    matched_skills = serializers.SerializerMethodField(read_only=True)
    missing_skills = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = Application
        fields = [
            'id', 'candidate_name', 'candidate_email',
            'job_title', 'status', 'status_display',
            'compatibility_score', 'matched_skills', 'missing_skills',
            'ai_summary', 'applied_at',
        ]

    def get_candidate_name(self, obj):
        return obj.candidate.get_full_name()

    def get_candidate_email(self, obj):
        return obj.candidate.email

    def get_job_title(self, obj):
        return obj.job_offer.title

    def get_matched_skills(self, obj):
        return obj.score_details.get('matched_skills', []) if obj.score_details else []

    def get_missing_skills(self, obj):
        return obj.score_details.get('missing_skills', []) if obj.score_details else []

    def get_status_display(self, obj):
        return obj.get_status_display()
