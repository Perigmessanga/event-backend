from rest_framework import serializers
from .models import Order
from apps.events.serializers import EventListSerializer
from apps.authentication.serializers import UserSerializer

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = EventListSerializer(read_only=True)
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'event', 'ticket_type', 'quantity',
            'total_price', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'total_price']

    def validate(self, data):
        quantity = data.get('quantity')
        if quantity <= 0:
            raise serializers.ValidationError({'quantity': 'Quantity must be greater than 0'})
        return data

    def create(self, validated_data):
        # Calcul du prix total basé sur ticket_type
        ticket_type = validated_data['ticket_type']
        validated_data['total_price'] = ticket_type.price * validated_data['quantity']
        return super().create(validated_data)