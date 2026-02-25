from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from .models import Event, Category, TicketType
from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateUpdateSerializer,
    CategorySerializer,
    TicketTypeSerializer
)
from .permissions import IsAdminOrReadOnly

# =========================================
# CATEGORY VIEWSET
# =========================================
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

# =========================================
# TICKET TYPE VIEWSET
# =========================================
class TicketTypeViewSet(viewsets.ModelViewSet):
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

# =========================================
# EVENT VIEWSET
# =========================================
class EventViewSet(viewsets.ModelViewSet):
    """
    Event API:
    - GET /events/
    - POST /events/
    - GET /events/{id}/
    - PATCH /events/{id}/
    - DELETE /events/{id}/
    - GET /events/my_events/
    - GET /events/published/
    - GET /events/upcoming/
    - GET /events/{id}/availability/
    """
    queryset = Event.objects.select_related("organizer", "category").all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'location']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_date', 'created_at', 'ticket_price']
    ordering = ['-start_date']

    permission_classes = [IsAdminOrReadOnly]

    # =========================================
    # SERIALIZER SWITCH
    # =========================================
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        return EventListSerializer

    # =========================================
    # QUERYSET LOGIC
    # =========================================
    def get_queryset(self):
        user = self.request.user
        if self.action == 'list':
            return Event.objects.filter(status='published').order_by('-start_date')
        if self.action == 'my_events':
            if user.is_authenticated:
                return Event.objects.filter(organizer=user).order_by('-start_date')
            return Event.objects.none()
        return Event.objects.all().order_by('-start_date')

    # =========================================
    # CREATE
    # =========================================
    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    # =========================================
    # CUSTOM ACTIONS
    # =========================================
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_events(self, request):
        events = Event.objects.filter(organizer=request.user).order_by('-start_date')
        serializer = EventListSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def published(self, request):
        events = Event.objects.filter(status='published').order_by('-start_date')
        serializer = EventListSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def upcoming(self, request):
        now = timezone.now()
        thirty_days_later = now + timedelta(days=30)
        events = Event.objects.filter(
            status='published',
            start_date__gte=now,
            start_date__lte=thirty_days_later
        ).order_by('start_date')
        serializer = EventListSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        event = self.get_object()
        if event.organizer != request.user and not request.user.is_staff:
            return Response({'error': 'Only the organizer can publish this event'}, status=status.HTTP_403_FORBIDDEN)
        event.status = 'published'
        event.save()
        return Response({'message': 'Event published successfully',
                         'event': EventDetailSerializer(event, context={'request': request}).data})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        event = self.get_object()
        if event.organizer != request.user and not request.user.is_staff:
            return Response({'error': 'Only the organizer can cancel this event'}, status=status.HTTP_403_FORBIDDEN)
        event.status = 'cancelled'
        event.save()
        return Response({'message': 'Event cancelled successfully',
                         'event': EventDetailSerializer(event, context={'request': request}).data})

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def availability(self, request, pk=None):
        event = self.get_object()
        tickets_sold = event.get_tickets_sold()
        available = event.get_available_tickets()
        return Response({
            'event_id': event.id,
            'title': event.title,
            'capacity': event.capacity,
            'tickets_sold': tickets_sold,
            'tickets_available': available,
            'percentage_sold': int((tickets_sold / event.capacity * 100)) if event.capacity > 0 else 0,
            'is_available': available > 0,
        })