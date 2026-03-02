from rest_framework import serializers
from .models import Order
from apps.events.models import Event, TicketType
from apps.authentication.serializers import UserSerializer

class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = ['id', 'name', 'price', 'available']

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'start_date', 'end_date']

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)
    ticket_type = TicketTypeSerializer(read_only=True)

    # Pour permettre la création via IDs
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(), write_only=True, source='event'
    )
    ticket_type_id = serializers.PrimaryKeyRelatedField(
        queryset=TicketType.objects.all(), write_only=True, source='ticket_type'
    )

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'event', 'ticket_type', 'quantity',
            'total_price', 'status', 'created_at', 'updated_at',
            'event_id', 'ticket_type_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'total_price']

    def validate(self, data):
        quantity = data.get('quantity')
        if quantity <= 0:
            raise serializers.ValidationError({'quantity': 'Quantity must be greater than 0'})
        return data

    def create(self, validated_data):
        ticket_type = validated_data['ticket_type']
        validated_data['total_price'] = ticket_type.price * validated_data['quantity']
        return super().create(validated_data)