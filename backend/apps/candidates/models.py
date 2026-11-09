"""
SmartRecruit AI — Modèles Candidature et CV
"""

import os
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


def cv_upload_path(instance, filename):
    """Génère un chemin d'upload sécurisé pour les CV."""
    ext = filename.split('.')[-1]
    return f"cvs/user_{instance.candidate.id}/{filename}"


def validate_pdf(value):
    """Valide que le fichier uploadé est bien un PDF."""
    ext = os.path.splitext(value.name)[1].lower()
    if ext != '.pdf':
        raise ValidationError("Seuls les fichiers PDF sont acceptés.")
    if value.size > settings.MAX_CV_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            f"Le fichier ne doit pas dépasser {settings.MAX_CV_SIZE_MB} Mo."
        )


class CandidateProfile(models.Model):
    """Profil étendu d'un candidat (lié au modèle User)."""

    user            = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='candidate_profile',
        verbose_name="Utilisateur"
    )
    headline        = models.CharField(max_length=255, blank=True, verbose_name="Titre professionnel")
    summary         = models.TextField(blank=True, verbose_name="Résumé")
    linkedin_url    = models.URLField(blank=True, verbose_name="LinkedIn")
    github_url      = models.URLField(blank=True, verbose_name="GitHub")
    portfolio_url   = models.URLField(blank=True, verbose_name="Portfolio")
    location        = models.CharField(max_length=150, blank=True, verbose_name="Localisation")
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidate_profiles'
        verbose_name        = 'Profil candidat'
        verbose_name_plural = 'Profils candidats'

    def __str__(self):
        return f"Profil de {self.user.get_full_name()}"


class CV(models.Model):
    """CV uploadé par un candidat."""

    class ProcessingStatus(models.TextChoices):
        PENDING    = 'pending',    'En attente'
        PROCESSING = 'processing', 'En cours d\'analyse'
        DONE       = 'done',       'Analysé'
        FAILED     = 'failed',     'Échec'

    candidate       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cvs',
        verbose_name="Candidat"
    )
    file            = models.FileField(
        upload_to=cv_upload_path,
        validators=[validate_pdf],
        verbose_name="Fichier PDF"
    )
    original_name   = models.CharField(max_length=255, verbose_name="Nom original du fichier")
    file_size       = models.PositiveIntegerField(verbose_name="Taille (octets)")
    is_primary      = models.BooleanField(default=False, verbose_name="CV principal")

    # ── Données extraites par l'IA ───────────────────────────────────────────────
    extracted_text  = models.TextField(blank=True, verbose_name="Texte extrait")
    extracted_data  = models.JSONField(default=dict, verbose_name="Données structurées extraites")
    # Structure de extracted_data:
    # {
    #   "name": str, "email": str, "phone": str,
    #   "skills": [...], "education": [...], "experience": [...],
    #   "languages": [...], "certifications": [...]
    # }

    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        verbose_name="Statut d'analyse"
    )
    processing_error  = models.TextField(blank=True, verbose_name="Erreur d'analyse")

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'cvs'
        verbose_name        = 'CV'
        verbose_name_plural = 'CVs'
        ordering            = ['-created_at']

    def __str__(self):
        return f"CV de {self.candidate.get_full_name()} — {self.original_name}"

    def save(self, *args, **kwargs):
        # Un seul CV principal par candidat
        if self.is_primary:
            CV.objects.filter(candidate=self.candidate, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class Application(models.Model):
    """Candidature d'un candidat à une offre d'emploi."""

    class Status(models.TextChoices):
        RECEIVED   = 'received',   'Reçue'
        ANALYZING  = 'analyzing',  'En cours d\'analyse'
        REVIEWED   = 'reviewed',   'Examinée'
        SHORTLISTED= 'shortlisted','Présélectionnée'
        ACCEPTED   = 'accepted',   'Acceptée'
        REJECTED   = 'rejected',   'Refusée'

    # ── Relations ────────────────────────────────────────────────────────────────
    candidate       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Candidat"
    )
    job_offer       = models.ForeignKey(
        'jobs.JobOffer',
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Offre d'emploi"
    )
    cv              = models.ForeignKey(
        CV,
        on_delete=models.SET_NULL,
        null=True,
        related_name='applications',
        verbose_name="CV soumis"
    )

    # ── Statut ───────────────────────────────────────────────────────────────────
    status          = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
        verbose_name="Statut"
    )
    cover_letter    = models.TextField(blank=True, verbose_name="Lettre de motivation")

    # ── Score IA ─────────────────────────────────────────────────────────────────
    compatibility_score = models.FloatField(
        null=True, blank=True,
        verbose_name="Score de compatibilité (0-100)"
    )
    score_details   = models.JSONField(
        default=dict,
        verbose_name="Détails du score"
    )
    # Structure de score_details:
    # {
    #   "skills_score": float, "experience_score": float, "education_score": float,
    #   "matched_skills": [...], "missing_skills": [...], "summary": str
    # }
    ai_summary      = models.TextField(blank=True, verbose_name="Résumé IA du profil")

    # ── Métadonnées ──────────────────────────────────────────────────────────────
    applied_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    recruiter_notes = models.TextField(blank=True, verbose_name="Notes recruteur")

    class Meta:
        db_table            = 'applications'
        verbose_name        = 'Candidature'
        verbose_name_plural = 'Candidatures'
        unique_together     = ('candidate', 'job_offer')   # une seule candidature par offre
        ordering            = ['-compatibility_score', '-applied_at']

    def __str__(self):
        return (
            f"{self.candidate.get_full_name()} → {self.job_offer.title} "
            f"[{self.status}] score={self.compatibility_score}"
        )
