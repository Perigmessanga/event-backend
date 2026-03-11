from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from apps.events.views import awdpay_webhook
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

# Simple endpoint pour vérifier si le backend tourne
def home(request):
    return HttpResponse("API EVENT MANAGER - Backend is running 🚀")

urlpatterns = [
    # Home
    path('', home, name='home'),

    # Admin
    path('admin/', admin.site.urls),

    # API Schema & Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1 - Authentification
    path('api/v1/auth/', include('apps.authentication.urls')),

    # API v1 - Gestion des événements
    path('api/v1/events/', include('apps.events.urls')),

    # API v1 - Commandes et Paiements
    path('api/v1/orders/', include('apps.orders.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path("api/contact/", include("apps.contact.urls")),
    path('api/v1/tickets/', include('apps.tickets.urls')),
    path('api/awdpay/webhook/', awdpay_webhook, name='awdpay_webhook'), # type: ignore

    # API v1 - Notifications (si besoin)
   # path('api/v1/notifications/', include('apps.notifications.urls')),

    # API v1 - Audit/logging (optionnel mais utile pour un système admin)
    #path('api/v1/audit/', include('apps.audit.urls')),
]

# Servir les fichiers médias en debug
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

