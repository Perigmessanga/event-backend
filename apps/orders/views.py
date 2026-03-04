from rest_framework import viewsets, permissions
from .models import Order
from .serializers import OrderSerializer, AdminOrderSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters



class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes= [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [p() for p in permission_classes]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.select_related(
        "user", "event", "ticket_type"
    )
    serializer_class = AdminOrderSerializer
    permission_classes = [permissions.IsAdminUser]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ["status", "event"]
    search_fields = ["user__email", "event__title"]
    ordering_fields = ["created_at", "total_price"]
    ordering = ["-created_at"]