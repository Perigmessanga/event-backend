from django.db import models, transaction
from apps.orders.models import Order
from apps.tickets.models import Ticket

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=255, unique=True)
    awdpay_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new_or_just_completed = self.pk is None or (
                self.status == 'completed' and 
                not Payment.objects.filter(pk=self.pk, status='completed').exists()
            )
            super().save(*args, **kwargs)

            if is_new_or_just_completed:
                self.order.status = 'paid'
                self.order.save()
                
                # Génère les tickets
                for _ in range(self.order.quantity):
                    Ticket.objects.create(
                        order=self.order,
                        event=self.order.event,
                        user=self.order.user,
                        ticket_type=self.order.ticket_type
                    )