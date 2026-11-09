"""
SmartRecruit AI — Vues Authentification
"""

import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    UserRegisterSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    CustomTokenObtainPairSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Inscription d'un nouveau candidat ou recruteur.
    """
    queryset         = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Email de bienvenue (asynchrone en production via Celery)
        try:
            send_mail(
                subject="Bienvenue sur SmartRecruit AI",
                message=(
                    f"Bonjour {user.get_full_name()},\n\n"
                    "Votre compte SmartRecruit AI a bien été créé.\n"
                    "Vous pouvez dès maintenant vous connecter et explorer les offres disponibles.\n\n"
                    "L'équipe SmartRecruit AI"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass  # L'email est non-bloquant

        return Response(
            {
                "message": "Compte créé avec succès.",
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Connexion et obtention des tokens JWT (access + refresh).
    Retourne également les informations de l'utilisateur connecté.
    """
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Déconnexion : blackliste le refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"error": "Le refresh token est requis."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Déconnexion réussie."},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"error": "Token invalide ou déjà expiré."},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/auth/profile/  — Consulter son profil
    PUT  /api/v1/auth/profile/  — Mettre à jour son profil
    PATCH /api/v1/auth/profile/ — Mise à jour partielle
    """
    serializer_class   = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    PUT /api/v1/auth/change-password/
    Changement de mot de passe pour l'utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response(
            {"message": "Mot de passe modifié avec succès."},
            status=status.HTTP_200_OK
        )


class PasswordResetRequestView(APIView):
    """
    POST /api/v1/auth/password-reset/
    Demande de réinitialisation — envoie un token par email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Réponse identique que l'email existe ou non (sécurité anti-énumération)
        generic_response = Response(
            {
                "message": (
                    "Si cet email est enregistré, vous recevrez "
                    "un lien de réinitialisation dans quelques minutes."
                )
            },
            status=status.HTTP_200_OK,
        )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return generic_response

        # Génération d'un token sécurisé (32 octets = 64 caractères hex)
        token = secrets.token_hex(32)
        user.reset_token         = token
        user.reset_token_expires = timezone.now() + timedelta(hours=1)
        user.save(update_fields=['reset_token', 'reset_token_expires'])

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        try:
            send_mail(
                subject="Réinitialisation de votre mot de passe SmartRecruit AI",
                message=(
                    f"Bonjour {user.get_full_name()},\n\n"
                    "Vous avez demandé la réinitialisation de votre mot de passe.\n"
                    f"Cliquez sur ce lien (valable 1 heure) :\n{reset_url}\n\n"
                    "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n\n"
                    "L'équipe SmartRecruit AI"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass

        return generic_response


class PasswordResetConfirmView(APIView):
    """
    POST /api/v1/auth/password-reset/confirm/
    Confirmation de la réinitialisation avec le token reçu.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        user.set_password(serializer.validated_data['new_password'])
        user.reset_token         = None
        user.reset_token_expires = None
        user.save()

        return Response(
            {"message": "Mot de passe réinitialisé avec succès. Vous pouvez vous connecter."},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    GET /api/v1/auth/me/
    Retourne les informations de l'utilisateur actuellement connecté.
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)
