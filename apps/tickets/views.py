from rest_framework import viewsets, permissions
from .models import Ticket
from .serializers import TicketSerializer

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related('event', 'ticket_type', 'user').all()
    serializer_class = TicketSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [p() for p in permission_classes]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)