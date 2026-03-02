import uuid
from django.db import models
from django.conf import settings

class Ticket(models.Model):
    
    order = models.ForeignKey(
        'orders.Order',
        related_name='tickets',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    event = models.ForeignKey(
        'events.Event',
        related_name='tickets',
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='tickets',
        on_delete=models.CASCADE
    )

    ticket_type = models.ForeignKey(
        'events.TicketType',
        related_name='tickets',
        on_delete=models.CASCADE
    )

    unique_code = models.UUIDField(default=uuid.uuid4, editable=False)
    is_used = models.BooleanField(default=False)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.user.username} - {self.ticket_type.name} ({self.unique_code})"