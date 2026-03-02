from django.db import models
from django.utils import timezone
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Event(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_events'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    image = models.ImageField(upload_to='events/posters/', null=True, blank=True)
    location = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    capacity = models.IntegerField()
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'events'
        ordering = ['-start_date']

    def __str__(self):
        return self.title

    # ------------------------------
    # Tickets
    # ------------------------------
    def get_tickets_sold(self):
        
        from apps.orders.models import Order
        return Order.objects.filter(event=self, status='confirmed').count()

    def get_available_tickets(self):
        return max(0, self.capacity - self.get_tickets_sold())

    @property
    def tickets_remaining(self):
        return self.get_available_tickets()

    @property
    def is_available(self):
        now = timezone.now()
        return self.status == 'published' and self.tickets_remaining > 0 and self.start_date > now

    # ------------------------------
    # URL complète pour les images
    # ------------------------------
    def image_url(self):
        if self.image:
            return self.image.url  # Si nécessaire, builder côté serializer avec request.build_absolute_uri
        return None

class TicketType(models.Model):
    event = models.ForeignKey(
        Event,
        related_name='ticket_types',
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity_total = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)

    max_per_order = models.PositiveIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        unique_together = ('event', 'name')

    @property
    def available(self):
        total = self.quantity_total or 0
        sold = self.quantity_sold or 0
        return total - sold

    def __str__(self):
        return f"{self.event.title} - {self.name}"

