from rest_framework import serializers
from apps.tickets.models import Ticket
from apps.events.serializers import TicketTypeSerializer
from apps.authentication.serializers import UserSerializer


class TicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    ticket_type_detail = TicketTypeSerializer(source='ticket_type', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id',
            'event',
            'user',
            'ticket_type',
            'ticket_type_detail',
            
            'purchased_at',
            
        ]
        read_only_fields = ['id', 'user', 'purchased_at']