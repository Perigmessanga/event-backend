from rest_framework import serializers
from .models import Payment
from apps.orders.serializers import OrderSerializer

class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'amount', 'status',
            'payment_method', 'transaction_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'amount']

    def create(self, validated_data):
        order = validated_data['order']
        validated_data['amount'] = order.total_price
        return super().create(validated_data)