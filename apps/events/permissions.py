from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    - Lecture autorisée pour tout le monde.
    - Création / modification / suppression réservées aux admins (is_staff).
    """

    def has_permission(self, request, view):
        # Lecture autorisée
        if request.method in permissions.SAFE_METHODS:
            return True

        # Écriture réservée aux admins authentifiés
        return request.user and request.user.is_authenticated and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Lecture autorisée
        if request.method in permissions.SAFE_METHODS:
            return True

        # Écriture réservée aux admins
        return request.user and request.user.is_authenticated and request.user.is_staff