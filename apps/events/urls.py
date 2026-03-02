# apps/events/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, CategoryViewSet

# Création du router pour gérer automatiquement les endpoints CRUD
router = DefaultRouter()
router.register(r'', EventViewSet, basename='events')       # /api/v1/events/
router.register(r'categories', CategoryViewSet, basename='categories')  # /api/v1/events/categories/

# URLs finales
urlpatterns = [
    path('', include(router.urls)),
]