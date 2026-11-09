"""
SmartRecruit AI — Modèles Offres d'emploi
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class JobOffer(models.Model):
    """Offre d'emploi publiée par un recruteur."""

    class ContractType(models.TextChoices):
        CDI       = 'CDI',       'CDI'
        CDD       = 'CDD',       'CDD'
        STAGE     = 'Stage',     'Stage'
        FREELANCE = 'Freelance', 'Freelance'
        ALTERNANCE= 'Alternance','Alternance'

    class Status(models.TextChoices):
        ACTIVE   = 'active',   'Active'
        CLOSED   = 'closed',   'Clôturée'
        DRAFT    = 'draft',    'Brouillon'

    class ExperienceLevel(models.TextChoices):
        JUNIOR   = 'junior',   'Junior (0-2 ans)'
        MID      = 'mid',      'Intermédiaire (2-5 ans)'
        SENIOR   = 'senior',   'Senior (5+ ans)'

    # ── Informations principales ─────────────────────────────────────────────────
    title           = models.CharField(max_length=255, verbose_name="Titre du poste")
    description     = models.TextField(verbose_name="Description")
    required_skills = models.JSONField(default=list, verbose_name="Compétences requises")
    location        = models.CharField(max_length=150, verbose_name="Localisation")
    contract_type   = models.CharField(
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.CDI,
        verbose_name="Type de contrat"
    )
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.MID,
        verbose_name="Niveau d'expérience"
    )
    sector          = models.CharField(max_length=100, blank=True, verbose_name="Secteur")
    salary_min      = models.PositiveIntegerField(null=True, blank=True, verbose_name="Salaire min (TND)")
    salary_max      = models.PositiveIntegerField(null=True, blank=True, verbose_name="Salaire max (TND)")

    # ── Statut et dates ──────────────────────────────────────────────────────────
    status          = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Statut"
    )
    expires_at      = models.DateTimeField(null=True, blank=True, verbose_name="Date d'expiration")
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    # ── Relations ────────────────────────────────────────────────────────────────
    recruiter       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_offers',
        verbose_name="Recruteur"
    )

    class Meta:
        db_table            = 'job_offers'
        verbose_name        = "Offre d'emploi"
        verbose_name_plural = "Offres d'emploi"
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.location} ({self.contract_type})"

    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def auto_close_if_expired(self):
        """Clôture automatiquement l'offre si la date d'expiration est dépassée."""
        if self.is_expired() and self.status == self.Status.ACTIVE:
            self.status = self.Status.CLOSED
            self.save(update_fields=['status'])
