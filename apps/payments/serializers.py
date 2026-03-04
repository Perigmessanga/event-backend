from rest_framework import serializers
from .models import Payment

from apps.orders.models import Order

class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), source='order', write_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'id',
            'order_id',
            'amount',
            'status',
            'payment_method',
            'transaction_id',
            'awdpay_transaction_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at', 'transaction_id', 'awdpay_transaction_id']


class AdminPaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="order.user.email", read_only=True)
    event_title = serializers.CharField(source="order.event.title", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "transaction_id",
            "user_email",
            "event_title",
            "amount",
            "payment_method",
            "status",
            "created_at",
        ]

