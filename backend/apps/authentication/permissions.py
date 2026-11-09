"""
SmartRecruit AI — Permissions personnalisées
"""

from rest_framework.permissions import BasePermission


class IsCandidat(BasePermission):
    """Autorise uniquement les utilisateurs avec le rôle CANDIDAT."""
    message = "Accès réservé aux candidats."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_candidat)


class IsRecruteur(BasePermission):
    """Autorise uniquement les utilisateurs avec le rôle RECRUTEUR."""
    message = "Accès réservé aux recruteurs."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_recruteur)


class IsAdmin(BasePermission):
    """Autorise uniquement les administrateurs."""
    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsRecruteurOrAdmin(BasePermission):
    """Autorise les recruteurs et les administrateurs."""
    message = "Accès réservé aux recruteurs et administrateurs."

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.is_recruteur or request.user.is_admin)
        )


class IsOwnerOrAdmin(BasePermission):
    """Autorise le propriétaire de l'objet ou un administrateur."""
    message = "Vous n'avez pas la permission d'accéder à cette ressource."

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        # Supporte les objets avec 'user', 'candidate', 'recruiter' ou directement l'utilisateur
        owner = (
            getattr(obj, 'user', None)
            or getattr(obj, 'candidate', None)
            or getattr(obj, 'recruiter', None)
            or obj
        )
        return owner == request.user
