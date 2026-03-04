from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .models import Payment
from rest_framework import generics
from .serializers import PaymentSerializer, AdminPaymentSerializer

from apps.orders.models import Order
import uuid

# =========================================
# Payment ViewSet pour React
# =========================================
class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Admin voit tous les paiements, utilisateur seulement les siens
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(order__user=user)

    # =========================================
    # Initiation du paiement (POST)
    # =========================================
    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate_payment(self, request):
        order_id = request.data.get('order_id')
        payment_method = request.data.get('payment_method')

        if not order_id or not payment_method:
            return Response(
                {"error": "order_id et payment_method requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": "Commande introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔒 Vérifier si déjà payée
        if hasattr(order, 'payment') and order.payment.status == 'completed':
            return Response(
                {"error": "Cette commande est déjà payée"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # 🔒 Vérifier si un paiement pending existe déjà
        existing_payment = Payment.objects.filter(
            order=order,
            status='pending'
        ).first()

        if existing_payment:
            serializer = PaymentSerializer(existing_payment)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # 🔐 Création transactionnelle
        with transaction.atomic():
            payment = Payment.objects.create(
                order=order,
                amount=order.total_price,
                payment_method=payment_method,
                transaction_id=str(uuid.uuid4()),
                status='pending'
            )

        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # =========================================
    # Vérifier le statut d'un paiement
    # =========================================
    @action(detail=True, methods=['get'], url_path='status')
    def check_status(self, request, pk=None):
        try:
            payment = self.get_object()
        except Payment.DoesNotExist:
            return Response({"error": "Paiement introuvable"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "id": payment.id,
            "status": payment.status,
            "transaction_id": payment.transaction_id,
            "order_id": payment.order.id,
        })


# =========================================
# Webhook externe (AWDPAY ou autre prestataire)
# =========================================
class PaymentWebhookView(APIView):
    permission_classes = []  # ouvert au prestataire

    def post(self, request):
        transaction_id = request.data.get('transaction_id')
        status_tx = request.data.get('status')

        try:
            with transaction.atomic():
                payment = Payment.objects.get(transaction_id=transaction_id)
                if status_tx.lower() == 'completed':
                    payment.status = 'completed'
                    payment.order.status = 'confirmed'  # ou 'paid', selon ton choix
                    payment.order.save()
                    payment.save()
                elif status_tx.lower() == 'failed':
                    payment.status = 'failed'
                    payment.save()
            return Response({"message": "Webhook reçu"}, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "Paiement inconnu"}, status=status.HTTP_404_NOT_FOUND)

    class AdminPaymentViewSet(viewsets.ReadOnlyModelViewSet):
        queryset = Payment.objects.select_related("order__user", "order__event")
        serializer_class = AdminPaymentSerializer
        permission_classes = [permissions.IsAdminUser]

            

