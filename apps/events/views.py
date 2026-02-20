from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from .models import Event
from .serializers import EventListSerializer, EventDetailSerializer, EventCreateUpdateSerializer
from apps import events 

class IsOrganizerOrReadOnly(permissions.BasePermission):
    """Allow only organizers to edit their events"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer == request.user


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing events
    - List: GET /api/v1/events/
    - Create: POST /api/v1/events/
    - Detail: GET /api/v1/events/{id}/
    - Update: PUT/PATCH /api/v1/events/{id}/
    - Delete: DELETE /api/v1/events/{id}/
    - My Events: GET /api/v1/events/my-events/
    - Published: GET /api/v1/events/published/
    - Upcoming: GET /api/v1/events/upcoming/
    - Availability: GET /api/v1/events/{id}/availability/
    """
    queryset = Event.objects.all().order_by('-start_date')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'organizer', 'location']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_date', 'created_at', 'ticket_price']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'retrieve':
            return EventDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        return EventListSerializer
    
    def get_queryset(self):
        user = self.request.user

    # Liste publique → seulement events publiés
        if self.action == 'list':
         return Event.objects.filter(status='published').order_by('-start_date')

    # Mes événements
        if self.action == 'my_events':
         if user.is_authenticated:
            return Event.objects.filter(organizer=user).order_by('-start_date')
        return Event.objects.none()

    # Détail / update / delete
        return Event.objects.all().order_by('-start_date')

    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOrganizerOrReadOnly]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_events(self, request):
        events = Event.objects.filter(organizer=request.user).order_by('-start_date')
        serializer = EventListSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def published(self, request):
        """Get all published events"""
        events = Event.objects.filter(status='published').order_by('-start_date')
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def upcoming(self, request):
        """Get upcoming events in the next 30 days"""
        now = timezone.now()
        thirty_days_later = now + timedelta(days=30)
        
        events = Event.objects.filter(
            status='published',
            start_date__gte=now,
            start_date__lte=thirty_days_later
        ).order_by('start_date')
        
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        """Publish an event (only for organizer)"""
        event = self.get_object()
        if event.organizer != request.user:
            return Response(
                {'error': 'Only the organizer can publish this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        event.status = 'published'
        event.save()
        return Response({
            'message': 'Event published successfully',
            'event': EventDetailSerializer(event, context={'request': request}).data

        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        """Cancel an event (only for organizer)"""
        event = self.get_object()
        if event.organizer != request.user:
            return Response(
                {'error': 'Only the organizer can cancel this event'},
                status=status.HTTP_403_FORBIDDEN
            )
        event.status = 'cancelled'
        event.save()
        return Response({
            'message': 'Event cancelled successfully',
            'event': EventDetailSerializer(event, context={'request': request}).data

        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def availability(self, request, pk=None):
        """Check ticket availability for an event"""
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
        }, status=status.HTTP_200_OK)
