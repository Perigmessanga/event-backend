from rest_framework import viewsets, permissions, status
from django.db import transaction
from rest_framework.response import Response
from decimal import Decimal
from .models import Order
from .serializers import OrderSerializer, AdminOrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [p() for p in permission_classes]

    def create(self, request, *args, **kwargs):
        items = request.data.get("items", [])

        if not items:
            return Response({"error": "Panier vide"}, status=400)

        first_item = items[0]

        with transaction.atomic():
            # Création de l'Order avec total_price temporaire 0
            order = Order.objects.create(
                user=request.user,
                event_id=first_item["eventId"],         # si requis par ton modèle
                ticket_type_id=first_item["ticketTypeId"],  # si requis
                status="pending",
                total_price=0
            )

            total_price = Decimal('0')

            # Création des OrderItems
            for item in items:
                order.items.create(
                    event_id=item["eventId"],
                    ticket_type_id=item["ticketTypeId"],
                    quantity=item["quantity"],
                    unit_price=item["unitPrice"]
                )
                

            total_price += Decimal(item["unitPrice"]) * Decimal(item["quantity"])

            # Mise à jour du total une seule fois
            order.total_price = total_price
            order.save()

        return Response({
            "id": order.id,
            "total_price": order.total_price
        }, status=201)
        
class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.select_related(
        "user", "event", "ticket_type"
    )
    serializer_class = AdminOrderSerializer
    permission_classes = [permissions.IsAdminUser]