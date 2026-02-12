from django.db import models


class Event(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    organizer = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='organized_events')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    location = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    capacity = models.IntegerField()
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'events'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    def get_tickets_sold(self):
        """Count total tickets sold for this event"""
        from apps.orders.models import Order
        return Order.objects.filter(event=self, status='completed').count()
    
    def get_available_tickets(self):
        """Get available tickets count"""
        return max(0, self.capacity - self.get_tickets_sold())
    
    @property
    def tickets_remaining(self):
        """Calculate remaining tickets"""
        return self.capacity - self.get_tickets_sold()
    
    @property
    def is_available(self):
        """Check if tickets are still available"""
        return self.status == 'published' and self.tickets_remaining > 0
