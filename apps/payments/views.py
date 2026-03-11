from rest_framework import viewsets, permissions, status
from rest_framework import response
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .models import Payment
from rest_framework import generics
from .serializers import PaymentSerializer, AdminPaymentSerializer
import requests
from django.conf import settings

from apps.orders.models import Order
import uuid

from io import BytesIO
from django.core.files import File
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db import transaction

from rest_framework.response import Response
from rest_framework import status
from apps.tickets.models import Ticket

from django.conf import settings
import qrcode  # Assure-toi que qrcode est installé

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
        if order.payment.filter(status='completed').exists():
            return Response(
                {"error": "Cette commande est déjà payée"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔒 Vérifier si un paiement pending existe déjà
        existing_payment = order.payment.filter(status='pending').first()
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

            # =========================
            # Appel AWDPAY
            # =========================
            payload = {
                "logo": "https://tonsite.com/logo.png",
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

            response = requests.post(
                "https://www.awdpay.com/api/checkout/v2/initiate",
                json=payload,
                headers=headers
            )

            data = response.json()

        return Response({
            "payment": PaymentSerializer(payment).data,
            "awdpay": data
        })

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
    permission_classes = []  # ouvert au prestataire (AWDPAY)

    def post(self, request):
        data = request.data
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

                    # 🔹 Génération automatique des tickets
                    # On suppose que chaque "OrderItem" correspond à un ticket
                    for item in payment.order.items.all():
                        ticket = Ticket.objects.create(
                            order=payment.order,
                            event=item.event,
                            user=payment.order.user,
                            ticket_type=item.ticket_type
                        )

                        # Le QR code est généré automatiquement dans Ticket.save()
                        # Si tu veux récupérer l'image pour le PDF ou email
                        tickets_files.append(ticket.qr_code.path)

                    # 🔹 Préparer l'email avec les tickets en PDF ou images
                    subject = f"Vos tickets pour la commande #{payment.order.id}"
                    message = render_to_string(
                        'emails/tickets_email.html',  # crée ce template
                        {'user': payment.order.user, 'order': payment.order, 'tickets': tickets_files}
                    )
                    email = EmailMessage(
                        subject=subject,
                        body=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[payment.order.user.email],
                    )
                    email.content_subtype = "html"

                    # Attacher les fichiers QR si besoin
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

