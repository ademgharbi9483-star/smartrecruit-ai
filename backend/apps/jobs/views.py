"""
SmartRecruit AI — Vues Offres d'emploi
"""

from django.utils import timezone
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.authentication.permissions import IsRecruteurOrAdmin, IsOwnerOrAdmin
from .models import JobOffer
from .serializers import (
    JobOfferSerializer,
    JobOfferListSerializer,
    JobOfferCreateUpdateSerializer,
)
from .filters import JobOfferFilter


class JobOfferListView(generics.ListAPIView):
    """
    GET /api/v1/jobs/
    Liste publique des offres actives avec filtres, recherche et tri.
    Accessible sans authentification.
    """
    serializer_class   = JobOfferListSerializer
    permission_classes = [AllowAny]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = JobOfferFilter
    search_fields      = ['title', 'description', 'required_skills', 'location', 'sector']
    ordering_fields    = ['created_at', 'title', 'salary_min', 'salary_max']
    ordering           = ['-created_at']

    def get_queryset(self):
        # Auto-clôture des offres expirées avant affichage
        expired_offers = JobOffer.objects.filter(
            status=JobOffer.Status.ACTIVE,
            expires_at__lt=timezone.now()
        )
        for offer in expired_offers:
            offer.auto_close_if_expired()

        return JobOffer.objects.filter(
            status=JobOffer.Status.ACTIVE
        ).select_related('recruiter')


class JobOfferDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/jobs/<id>/
    Détail d'une offre d'emploi (lecture publique).
    """
    queryset           = JobOffer.objects.select_related('recruiter')
    serializer_class   = JobOfferSerializer
    permission_classes = [AllowAny]


class JobOfferCreateView(generics.CreateAPIView):
    """
    POST /api/v1/jobs/create/
    Création d'une nouvelle offre (recruteurs uniquement).
    """
    serializer_class   = JobOfferCreateUpdateSerializer
    permission_classes = [IsAuthenticated, IsRecruteurOrAdmin]

    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Retourner la vue complète après création
        full_serializer = JobOfferSerializer(serializer.instance)
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)


class JobOfferUpdateView(generics.UpdateAPIView):
    """
    PUT   /api/v1/jobs/<id>/update/
    PATCH /api/v1/jobs/<id>/update/
    Mise à jour d'une offre (propriétaire ou admin uniquement).
    """
    queryset           = JobOffer.objects.all()
    serializer_class   = JobOfferCreateUpdateSerializer
    permission_classes = [IsAuthenticated, IsRecruteurOrAdmin, IsOwnerOrAdmin]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def check_object_permissions(self, request, obj):
        # Vérifie que le recruteur est propriétaire de l'offre
        if not request.user.is_admin and obj.recruiter != request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous ne pouvez modifier que vos propres offres.")
        super().check_object_permissions(request, obj)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        full_serializer = JobOfferSerializer(serializer.instance)
        return Response(full_serializer.data)


class JobOfferDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/v1/jobs/<id>/delete/
    Suppression d'une offre (propriétaire ou admin).
    """
    queryset           = JobOffer.objects.all()
    permission_classes = [IsAuthenticated, IsRecruteurOrAdmin]

    def get_object(self):
        obj = super().get_object()
        if not self.request.user.is_admin and obj.recruiter != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous ne pouvez supprimer que vos propres offres.")
        return obj

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        title = instance.title
        self.perform_destroy(instance)
        return Response(
            {"message": f"L'offre « {title} » a été supprimée."},
            status=status.HTTP_200_OK
        )


class RecruiterJobOffersView(generics.ListAPIView):
    """
    GET /api/v1/jobs/my-offers/
    Liste des offres du recruteur connecté (toutes statuts).
    """
    serializer_class   = JobOfferListSerializer
    permission_classes = [IsAuthenticated, IsRecruteurOrAdmin]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class    = JobOfferFilter
    ordering_fields    = ['created_at', 'status', 'title']
    ordering           = ['-created_at']

    def get_queryset(self):
        return JobOffer.objects.filter(
            recruiter=self.request.user
        ).select_related('recruiter')


class JobOfferCloseView(APIView):
    """
    POST /api/v1/jobs/<id>/close/
    Clôture manuelle d'une offre.
    """
    permission_classes = [IsAuthenticated, IsRecruteurOrAdmin]

    def post(self, request, pk):
        try:
            offer = JobOffer.objects.get(pk=pk)
        except JobOffer.DoesNotExist:
            return Response({"error": "Offre introuvable."}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_admin and offer.recruiter != request.user:
            return Response(
                {"error": "Vous ne pouvez clôturer que vos propres offres."},
                status=status.HTTP_403_FORBIDDEN
            )

        if offer.status == JobOffer.Status.CLOSED:
            return Response(
                {"message": "Cette offre est déjà clôturée."},
                status=status.HTTP_400_BAD_REQUEST
            )

        offer.status = JobOffer.Status.CLOSED
        offer.save(update_fields=['status'])
        return Response(
            {"message": f"L'offre « {offer.title} » a été clôturée."},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def job_stats_view(request):
    """
    GET /api/v1/jobs/stats/
    Statistiques globales des offres (publiques).
    """
    total    = JobOffer.objects.count()
    active   = JobOffer.objects.filter(status=JobOffer.Status.ACTIVE).count()
    closed   = JobOffer.objects.filter(status=JobOffer.Status.CLOSED).count()

    by_contract = {}
    for ct in JobOffer.ContractType.values:
        by_contract[ct] = JobOffer.objects.filter(
            contract_type=ct, status=JobOffer.Status.ACTIVE
        ).count()

    return Response({
        "total":       total,
        "active":      active,
        "closed":      closed,
        "by_contract": by_contract,
    })
