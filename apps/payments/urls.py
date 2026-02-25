from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet
from .views import PaymentWebhookView

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]
