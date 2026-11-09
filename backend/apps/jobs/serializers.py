"""
SmartRecruit AI — Sérialiseurs Offres d'emploi
"""

from rest_framework import serializers
from django.utils import timezone
from .models import JobOffer


class JobOfferSerializer(serializers.ModelSerializer):
    """Sérialiseur complet pour les offres d'emploi."""

    recruiter_name      = serializers.SerializerMethodField(read_only=True)
    applications_count  = serializers.SerializerMethodField(read_only=True)
    is_expired          = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = JobOffer
        fields = [
            'id', 'title', 'description', 'required_skills',
            'location', 'contract_type', 'experience_level',
            'sector', 'salary_min', 'salary_max',
            'status', 'expires_at', 'created_at', 'updated_at',
            'recruiter', 'recruiter_name',
            'applications_count', 'is_expired',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'recruiter']

    def get_recruiter_name(self, obj):
        return obj.recruiter.get_full_name()

    def get_applications_count(self, obj):
        return obj.applications.count()

    def get_is_expired(self, obj):
        return obj.is_expired()

    def validate_required_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Les compétences doivent être une liste.")
        if len(value) == 0:
            raise serializers.ValidationError("Au moins une compétence requise est obligatoire.")
        if len(value) > 30:
            raise serializers.ValidationError("Maximum 30 compétences autorisées.")
        return [skill.strip() for skill in value if skill.strip()]

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("La date d'expiration doit être dans le futur.")
        return value

    def validate_salary_min(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Le salaire minimum ne peut pas être négatif.")
        return value

    def validate(self, attrs):
        salary_min = attrs.get('salary_min')
        salary_max = attrs.get('salary_max')
        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError(
                {"salary_min": "Le salaire minimum ne peut pas dépasser le salaire maximum."}
            )
        return attrs


class JobOfferListSerializer(serializers.ModelSerializer):
    """Sérialiseur allégé pour la liste des offres (performance)."""

    recruiter_name     = serializers.SerializerMethodField(read_only=True)
    applications_count = serializers.SerializerMethodField(read_only=True)
    is_expired         = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = JobOffer
        fields = [
            'id', 'title', 'location', 'contract_type', 'experience_level',
            'sector', 'required_skills', 'salary_min', 'salary_max',
            'status', 'expires_at', 'created_at',
            'recruiter_name', 'applications_count', 'is_expired',
        ]

    def get_recruiter_name(self, obj):
        return obj.recruiter.get_full_name()

    def get_applications_count(self, obj):
        return obj.applications.count()

    def get_is_expired(self, obj):
        return obj.is_expired()


class JobOfferCreateUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création et mise à jour d'une offre."""

    class Meta:
        model  = JobOffer
        fields = [
            'title', 'description', 'required_skills',
            'location', 'contract_type', 'experience_level',
            'sector', 'salary_min', 'salary_max',
            'status', 'expires_at',
        ]

    def validate_required_skills(self, value):
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError("Au moins une compétence est requise.")
        return [s.strip() for s in value if s.strip()]

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("La date d'expiration doit être dans le futur.")
        return value

    def validate(self, attrs):
        salary_min = attrs.get('salary_min')
        salary_max = attrs.get('salary_max')
        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError(
                {"salary_min": "Le salaire min ne peut pas dépasser le salaire max."}
            )
        return attrs
