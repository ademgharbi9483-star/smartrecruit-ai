"""
SmartRecruit AI — URLs principales
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ── Documentation Swagger ─────────────────────────────────────────────────────────
schema_view = get_schema_view(
    openapi.Info(
        title="SmartRecruit AI API",
        default_version='v1',
        description=(
            "API REST de la plateforme SmartRecruit AI — "
            "Recrutement automatisé et intelligent"
        ),
        contact=openapi.Contact(email="contact@smartrecruit.ai"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # Documentation API
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # APIs applicatives
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/jobs/', include('apps.jobs.urls')),
    path('api/v1/candidates/', include('apps.candidates.urls')),
    path('api/v1/ai/', include('apps.ai_engine.urls')),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
