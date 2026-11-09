"""
SmartRecruit AI — Modèle Utilisateur personnalisé
Remplace le modèle User Django par défaut avec gestion des rôles.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager personnalisé pour le modèle User."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Utilisateur SmartRecruit AI.
    Trois rôles : CANDIDAT, RECRUTEUR, ADMIN.
    """

    class Role(models.TextChoices):
        CANDIDAT   = 'candidat',   'Candidat'
        RECRUTEUR  = 'recruteur',  'Recruteur'
        ADMIN      = 'admin',      'Administrateur'

    # ── Champs identité ──────────────────────────────────────────────────────────
    email        = models.EmailField(unique=True, verbose_name="Adresse email")
    first_name   = models.CharField(max_length=100, verbose_name="Prénom")
    last_name    = models.CharField(max_length=100, verbose_name="Nom")
    phone        = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    avatar       = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # ── Rôle & statut ────────────────────────────────────────────────────────────
    role         = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CANDIDAT,
        verbose_name="Rôle"
    )
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)

    # ── Métadonnées ──────────────────────────────────────────────────────────────
    date_joined  = models.DateTimeField(default=timezone.now)
    last_login   = models.DateTimeField(null=True, blank=True)
    updated_at   = models.DateTimeField(auto_now=True)

    # ── Réinitialisation mot de passe ────────────────────────────────────────────
    reset_token           = models.CharField(max_length=255, blank=True, null=True)
    reset_token_expires   = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table    = 'users'
        verbose_name        = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_candidat(self):
        return self.role == self.Role.CANDIDAT

    @property
    def is_recruteur(self):
        return self.role == self.Role.RECRUTEUR

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
