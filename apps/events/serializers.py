from rest_framework import serializers
from .models import Event
from apps.authentication.serializers import UserSerializer


class EventListSerializer(serializers.ModelSerializer):
    """Simplified serializer for event list"""
    organizer = UserSerializer(read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'image', 'location',
            'start_date', 'end_date', 'capacity', 'ticket_price',
            'status', 'organizer', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'organizer']


class EventDetailSerializer(serializers.ModelSerializer):
    """Full serializer for event detail"""
    organizer = UserSerializer(read_only=True)
    tickets_available = serializers.SerializerMethodField()
    tickets_sold = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'image', 'location',
            'start_date', 'end_date', 'capacity', 'ticket_price',
            'status', 'organizer', 'created_at', 'updated_at',
            'tickets_available', 'tickets_sold'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'organizer']
    
    def get_tickets_available(self, obj):
        """Calculate available tickets"""
        return obj.capacity - obj.get_tickets_sold()
    
    def get_tickets_sold(self, obj):
        """Get number of tickets sold"""
        return obj.get_tickets_sold()


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating events"""
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'image', 'location',
            'start_date', 'end_date', 'capacity', 'ticket_price', 'status'
        ]
    
    def validate(self, data):
        """Validate event dates"""
        if data.get('start_date') >= data.get('end_date'):
            raise serializers.ValidationError('Start date must be before end date')
        if data.get('capacity', 0) <= 0:
            raise serializers.ValidationError('Capacity must be greater than 0')
        if data.get('ticket_price', 0) < 0:
            raise serializers.ValidationError('Ticket price cannot be negative')
        return data
