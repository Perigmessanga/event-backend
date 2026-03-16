# payments/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .models import Payment
from .serializers import PaymentSerializer
from apps.orders.models import Order
from apps.tickets.models import Ticket
import requests
import uuid
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import qrcode  # type: ignore

# =========================================
# Payment ViewSet pour React + Mock
# =========================================
class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(order__user=user)

    # -------------------------------
    # Initiation du paiement réel
    # -------------------------------
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
            return Response({"error": "Commande introuvable"}, status=status.HTTP_404_NOT_FOUND)

        # Déjà payée ?
        if order.payment.filter(status='completed').exists():
            return Response({"error": "Cette commande est déjà payée"}, status=status.HTTP_400_BAD_REQUEST)

        # Paiement pending existant ?
        existing_payment = order.payment.filter(status='pending').first()
        if existing_payment:
            serializer = PaymentSerializer(existing_payment)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Création transactionnelle
        with transaction.atomic():
            payment = Payment.objects.create(
                order=order,
                amount=order.total_price,
                payment_method=payment_method,
                transaction_id=str(uuid.uuid4()),
                status='pending'
            )

            # Appel AWDPAY
            payload = {
                "logo": "https://app.awdpay.pro/AWDsvg.png",
                "amount": float(order.total_price),
                "currency": "XAF",
                "customIdentifier": str(payment.transaction_id),
                "callbackUrl": f"{settings.BACKEND_URL}/api/payments/webhook/",
                "successUrl": f"{settings.FRONTEND_URL}/payment-success",
                "failedUrl": f"{settings.FRONTEND_URL}/payment-failed",
                "test": False
            }

            headers = {
                "Authorization": f"Bearer {settings.AWDPAY_PRIVATE_KEY}",
                "Content-Type": "application/json"
            }

            try:
                response = requests.post(
                    f"{settings.AWDPAY_BASE_URL}/initiate",
                    json=payload,
                    headers=headers,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                print("Erreur AWDPAY:", str(e))
                return Response({"error": "Impossible de contacter AWDPAY."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Debug console
            print("AWDPAY RAW RESPONSE:", response.text)

        return Response({
            "payment": PaymentSerializer(payment).data,
            "awdpay": {
                "checkoutUrl": data.get("checkout_url") or data.get("checkoutUrl") or None,
                "transactionId": data.get("transaction_id") or data.get("transactionId") or str(payment.transaction_id)
            }
        })

    # -------------------------------
    # Vérification du statut d'un paiement
    # -------------------------------
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

    # -------------------------------
    # Endpoint Mock AWDPAY pour tests
    # -------------------------------
    @action(detail=False, methods=['post'], url_path='mock')
    def mock_payment(self, request):
        amount = request.data.get('amount')
        currency = request.data.get('currency')
        user_id = request.data.get('user_id')

        if not all([amount, currency, user_id]):
            return Response({"error": "amount, currency et user_id requis"},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "status": "success",
            "transaction_id": str(uuid.uuid4()),
            "amount": amount,
            "currency": currency,
            "user_id": user_id
        })


# =========================================
# Webhook AWDPAY pour prod
# =========================================
class PaymentWebhookView(APIView):
    permission_classes = []  # ouvert à AWDPAY

    def post(self, request):
        transaction_id = request.data.get("customIdentifier")
        status_tx = request.data.get("status")

        if not transaction_id or not status_tx:
            return Response({"error": "Données manquantes"}, status=400)

        try:
            with transaction.atomic():
                payment = Payment.objects.select_related("order").get(transaction_id=transaction_id)

                if status_tx.lower() == "success":
                    payment.status = "completed"
                    payment.order.status = "confirmed"
                    payment.order.save()
                    payment.save()

                    tickets_files = []

                    # Génération automatique des tickets
                    for item in payment.order.items.all():
                        ticket = Ticket.objects.create(
                            order=payment.order,
                            event=item.event,
                            user=payment.order.user,
                            ticket_type=item.ticket_type
                        )
                        tickets_files.append(ticket.qr_code.path)

                    # Email avec tickets
                    subject = f"Vos tickets pour la commande #{payment.order.id}"
                    message = render_to_string(
                        'emails/tickets_email.html',
                        {'user': payment.order.user, 'order': payment.order, 'tickets': tickets_files}
                    )
                    email = EmailMessage(
                        subject=subject,
                        body=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[payment.order.user.email],
                    )
                    email.content_subtype = "html"

                    for qr_path in tickets_files:
                        with open(qr_path, 'rb') as f:
                            email.attach(f"{uuid.uuid4()}.png", f.read(), 'image/png')

                    email.send(fail_silently=True)

                elif status_tx.lower() == "failed":
                    payment.status = "failed"
                    payment.save()

            return Response({"message": "Webhook traité avec succès"}, status=200)

        except Payment.DoesNotExist:
            return Response({"error": "Paiement inconnu"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)