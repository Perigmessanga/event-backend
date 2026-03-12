# apps/orders/models.py

from django.db import models
from django.conf import settings
from django.forms import ValidationError


class Order(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='orders',
        on_delete=models.CASCADE
    )

    event = models.ForeignKey(
        'events.Event',  # ✅ référence en chaîne
        related_name='orders',
        on_delete=models.CASCADE
    )

    ticket_type = models.ForeignKey(
        'events.TicketType',  # ✅ référence en chaîne
        related_name='orders',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)

    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} by {self.user.username} ({self.status})"
    
    def clean(self):
        """Vérifie la capacité avant création"""
        if self.ticket_type and self.quantity > self.ticket_type.available:
            raise ValidationError("Quantité demandée supérieure à la disponibilité.")
        
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE)
    ticket_type = models.ForeignKey('events.TicketType', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
            