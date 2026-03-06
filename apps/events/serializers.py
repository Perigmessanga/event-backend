from rest_framework import serializers
from .models import Event, TicketType, Category
from apps.authentication.serializers import UserSerializer

# ==============================
# CATEGORY SERIALIZER
# ==============================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']

# ==============================
# TICKET TYPE SERIALIZER
# ==============================
class TicketTypeSerializer(serializers.ModelSerializer):
    available = serializers.IntegerField(read_only=True)

    class Meta:
        model = TicketType
        fields = [
            "id",
            "name",
            "description",
            "price",
            "available",
            "max_per_order",
        ]

# ==============================
# EVENT LIST SERIALIZER
# ==============================
class EventListSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'image_url', 'location',
            'start_date', 'end_date', 'capacity', 'ticket_price',
            'status', 'organizer', 'created_at', 'category',
        ]
        read_only_fields = ['id', 'created_at', 'organizer']

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

# ==============================
# EVENT DETAIL SERIALIZER
# ==============================
class EventDetailSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    ticket_types = TicketTypeSerializer(many=True, read_only=True)  # ← IMPORTANT
    image_url = serializers.SerializerMethodField()
    tickets_available = serializers.SerializerMethodField()
    tickets_sold = serializers.SerializerMethodField()
    total = serializers.CharField(source='id')


    

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'image_url', 'location',
            'start_date', 'end_date', 'capacity', 'ticket_price', 'status',
            'organizer', 'created_at', 'updated_at',
            'tickets_available', 'tickets_sold', 'category', 'ticket_types','total'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'organizer']

    def get_total(self,obj):
        return True

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_tickets_sold(self, obj):
        return obj.get_tickets_sold() if hasattr(obj, "get_tickets_sold") else 0

    def get_tickets_available(self, obj):
        sold = self.get_tickets_sold(obj)
        return max(obj.capacity - sold, 0)

# ==============================
# EVENT CREATE / UPDATE SERIALIZER
# ==============================
class EventCreateUpdateSerializer(serializers.ModelSerializer):
    ticketTypes = TicketTypeSerializer(many=True, required=False)
    organizer = UserSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'image', 'location',
            'start_date', 'end_date', 'capacity', 'ticket_price', 'status',
            'category', 'organizer', 'ticketTypes'
        ]
        read_only_fields = ['organizer']

    # --------------------------
    # VALIDATION
    # --------------------------
    def validate(self, data):
        start = data.get('start_date')
        end = data.get('end_date')
        if start and end and start >= end:
            raise serializers.ValidationError({'end_date': 'Start date must be after start date'})
        if 'capacity' in data and data['capacity'] <= 0:
            raise serializers.ValidationError({'capacity': 'Capacity must be greater than 0'})
        if 'ticket_price' in data and data['ticket_price'] < 0:
            raise serializers.ValidationError({'ticket_price': 'Ticket price cannot be negative'})
        return data

    # --------------------------
    # CREATE
    # --------------------------
    def create(self, validated_data):
        ticket_data = validated_data.pop('ticketTypes', [])
        event = Event.objects.create(**validated_data)
        for ticket in ticket_data:
            TicketType.objects.create(event=event, **ticket)
        return event

    # --------------------------
    # UPDATE (PATCH SAFE)
    # --------------------------
    def update(self, instance, validated_data):
        ticket_data = validated_data.pop('ticketTypes', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if ticket_data is not None:
            instance.ticketTypes.all().delete()
            for ticket in ticket_data:
                TicketType.objects.create(event=instance, **ticket)
        return instance

class EventPublicDetailSerializer(serializers.ModelSerializer):
    ticketTypes = TicketTypeSerializer(
        many=True,
        read_only=True,
        source='ticket_types'   # 👈 LA CORRECTION ICI
    )

    class Meta:
        model = Event
        fields = "__all__"

        

class AdminTicketTypeSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source="event.title", read_only=True)

    class Meta:
        model = TicketType
        fields = "__all__"
        