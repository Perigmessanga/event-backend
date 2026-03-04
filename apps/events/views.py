from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Avg
from rest_framework.views import APIView
from apps.orders.models import Order
from datetime import datetime
from rest_framework import permissions
from django.db.models.functions import TruncMonth



from .models import Category, Event, TicketType
from .serializers import CategorySerializer, EventListSerializer, EventDetailSerializer, EventCreateUpdateSerializer

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    
class EventViewSet(viewsets.ModelViewSet):
    """
    Event API:
    - GET /events/             -> Liste publique (homepage)
    - POST /events/            -> Créer un événement
    - GET /events/{id}/        -> Détails d'un événement
    - PATCH /events/{id}/      -> Mise à jour
    - DELETE /events/{id}/     -> Suppression
    - GET /events/my_events/   -> Mes événements (connecté)
    - GET /events/published/   -> Événements publiés
    - GET /events/upcoming/    -> Événements à venir (30 jours)
    - POST /events/{id}/publish/
    - POST /events/{id}/cancel/
    - GET /events/{id}/availability/
    """
    queryset = Event.objects.select_related("organizer", "category").all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'category', 'location']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_date', 'created_at', 'ticket_price']
    ordering = ['-start_date']
    
    search_fields = ['title', 'description', 'location']

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # -------------------------
    # Choix du serializer selon l'action
    # -------------------------
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        return EventListSerializer

    # -------------------------
    # Queryset selon l'action et l'utilisateur
    # -------------------------
    def get_queryset(self):
        user = self.request.user

        # Liste publique
        if self.action == 'list':
            if user.is_authenticated and user.is_staff:
                return Event.objects.all().order_by('-start_date')
            return Event.objects.filter(status='published').order_by('-start_date')

        # Mes événements (connecté)
        if self.action == 'my_events':
            if user.is_authenticated:
                return Event.objects.filter(organizer=user).order_by('-start_date')
            return Event.objects.none()

        # Par défaut (retrieve, update, delete)
        return Event.objects.all().order_by('-start_date')

    # -------------------------
    # Création
    # -------------------------
    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    # -------------------------
    # Actions personnalisées
    # -------------------------
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
            return Response({'error': 'Seul l’organisateur peut publier cet événement'}, status=status.HTTP_403_FORBIDDEN)
        event.status = 'published'
        event.save()
        serializer = EventDetailSerializer(event, context={'request': request})
        return Response({'message': 'Événement publié avec succès', 'event': serializer.data})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        event = self.get_object()
        if event.organizer != request.user and not request.user.is_staff:
            return Response({'error': 'Seul l’organisateur peut annuler cet événement'}, status=status.HTTP_403_FORBIDDEN)
        event.status = 'cancelled'
        event.save()
        serializer = EventDetailSerializer(event, context={'request': request})
        return Response({'message': 'Événement annulé avec succès', 'event': serializer.data})

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

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def public_detail(self, request, pk=None):
        """
        Permet à un utilisateur de consulter un événement publié
        et d'avoir les informations nécessaires pour réserver un ticket.
        """
        event = self.get_object()

        # Vérifier que l'événement est publié
        if event.status != 'published':
            return Response({'error': "Cet événement n'est pas disponible."}, status=status.HTTP_403_FORBIDDEN)

        # Sérialisation complète pour le frontend
        serializer = EventDetailSerializer(event, context={'request': request})
        tickets_available = event.get_available_tickets()

        return Response({
            'event': serializer.data,
            'tickets_available': tickets_available,
            'can_book': tickets_available > 0
        }, status=status.HTTP_200_OK)

class AdminSalesView(APIView):
        permission_classes = [permissions.IsAdminUser]

        def get(self, request):

            # 📅 Filtres dynamiques
            start_date = request.GET.get("start_date")
            end_date = request.GET.get("end_date")

            orders = Order.objects.filter(status="confirmed")

            if start_date:
                orders = orders.filter(created_at__gte=start_date)

            if end_date:
                orders = orders.filter(created_at__lte=end_date)

            # 🔹 Totaux globaux
            total_revenue = orders.aggregate(total=Sum("total_price"))["total"] or 0
            total_tickets = orders.aggregate(total=Sum("quantity"))["total"] or 0
            average_cart = orders.aggregate(avg=Avg("total_price"))["avg"] or 0

            # 🔹 Top 5 événements
            top_events = (
                orders.values("event__title")
                .annotate(revenue=Sum("total_price"))
                .order_by("-revenue")[:5]
            )

            # 🔹 Evolution mensuelle
            monthly_sales = (
                orders.annotate(month=TruncMonth("created_at"))
                .values("month")
                .annotate(revenue=Sum("total_price"))
                .order_by("month")
            )

            # 🔹 Distribution billets (Pie Chart)
            ticket_distribution = (
                orders.values("ticket_type__name")
                .annotate(total=Sum("quantity"))
                .order_by("-total")
            )

            return Response({
                "total_revenue": total_revenue,
                "total_tickets": total_tickets,
                "average_cart": round(average_cart, 2),
                "top_events": top_events,
                "monthly_sales": monthly_sales,
                "ticket_distribution": ticket_distribution,
            })
