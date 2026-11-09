"""
SmartRecruit AI — Sérialiseurs Authentification
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    """Inscription d'un nouvel utilisateur."""

    password  = serializers.CharField(
        write_only=True, required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, required=True,
        style={'input_type': 'password'},
        label="Confirmation du mot de passe"
    )

    class Meta:
        model  = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'role', 'password', 'password2']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name':  {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Les deux mots de passe ne correspondent pas."}
            )
        # Seuls CANDIDAT et RECRUTEUR peuvent s'inscrire librement
        role = attrs.get('role', User.Role.CANDIDAT)
        if role == User.Role.ADMIN:
            raise serializers.ValidationError(
                {"role": "L'inscription en tant qu'administrateur n'est pas autorisée."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Lecture et mise à jour du profil utilisateur."""

    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'avatar', 'role', 'date_joined', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'updated_at']

    def get_full_name(self, obj):
        return obj.get_full_name()


class ChangePasswordSerializer(serializers.Serializer):
    """Changement de mot de passe (utilisateur connecté)."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, write_only=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "Les deux nouveaux mots de passe ne correspondent pas."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("L'ancien mot de passe est incorrect.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Demande de réinitialisation de mot de passe."""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        # On ne révèle pas si l'email existe pour éviter l'énumération
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirmation de la réinitialisation avec le token reçu par email."""

    token        = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, write_only=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "Les deux mots de passe ne correspondent pas."}
            )
        # Vérification du token
        try:
            user = User.objects.get(reset_token=attrs['token'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"token": "Token invalide ou expiré."})

        if user.reset_token_expires and user.reset_token_expires < timezone.now():
            raise serializers.ValidationError({"token": "Token expiré. Veuillez refaire une demande."})

        attrs['user'] = user
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT enrichi avec les données utilisateur."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Claims supplémentaires dans le payload JWT
        token['email']      = user.email
        token['full_name']  = user.get_full_name()
        token['role']       = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Ajouter les infos utilisateur dans la réponse
        data['user'] = {
            'id':         self.user.id,
            'email':      self.user.email,
            'full_name':  self.user.get_full_name(),
            'role':       self.user.role,
            'avatar':     self.user.avatar.url if self.user.avatar else None,
        }
        return data
