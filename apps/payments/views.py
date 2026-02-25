from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .models import Payment
from .serializers import PaymentSerializer

# =========================================
# PAYMENT VIEWSET (ReadOnly)
# =========================================
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(order__user=self.request.user)

    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate_payment(self, request):
        order_id = request.data.get('order_id')
        # Logique externe : appel prestataire, création Payment pending
        return Response({"checkout_url": "https://stripe.com/pay/...", "payment_id": "..."})

    @action(detail=False, methods=['post'], url_path='pay-with-awdpay')
    def pay_with_awdpay(self, request):
        order_id = request.data.get('order_id')
        user = request.user
        order = request.user.order_set.get(id=order_id)
        # Appel AWDPAY fictif
        response = call_awdpay_api(user_email=user.email, amount=order.total_price)
        if response.status == "INSUFFICIENT_FUNDS":
            return Response({"error": "Solde AWDPAY insuffisant"}, status=400)
        Payment.objects.create(order_id=order_id, amount=order.total_price,
                               transaction_id=response.awdpay_ref, status='pending')
        return Response({"message": "Paiement en cours", "ref": response.awdpay_ref})

# =========================================
# WEBHOOKS
# =========================================
class PaymentWebhookView(APIView):
    permission_classes = []

    def post(self, request):
        trans_id = request.data.get('transaction_id')
        try:
            with transaction.atomic():
                payment = Payment.objects.get(transaction_id=trans_id)
                if request.data.get('status') == 'completed':
                    payment.status = 'completed'
                    payment.save()
                return Response({"message": "Webhook reçu"}, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "Paiement inconnu"}, status=status.HTTP_404_NOT_FOUND)

class AWDPAYWebhookView(APIView):
    permission_classes = []

    def post(self, request):
        ref = request.data.get('awdpay_ref')
        status_tx = request.data.get('status')
        try:
            payment = Payment.objects.get(transaction_id=ref)
            if status_tx == 'SUCCESS':
                with transaction.atomic():
                    payment.status = 'completed'
                    payment.save()
                return Response(status=200)
        except Payment.DoesNotExist:
            return Response(status=404)