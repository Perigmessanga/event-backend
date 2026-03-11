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
    
    qr_code = models.ImageField(upload_to='tickets_qr/', blank=True, null=True)

    def generate_qr_code(self):
        qr = qrcode.QRCode( # type: ignore
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L, # type: ignore
            box_size=10,
            border=4,
        )
        qr.add_data(str(self.unique_code))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Sauvegarder dans ImageField
        buffer = BytesIO() # type: ignore
        img.save(buffer, 'PNG')
        filename = f"ticket-{self.unique_code}.png"
        self.qr_code.save(filename, File(buffer), save=False) # type: ignore
        buffer.close()
        return self.qr_code
    
        def save(self, *args, **kwargs):
            if not self.qr_code:
                self.generate_qr_code()
            super().save(*args, **kwargs)

    class Meta:
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.user.username} - {self.ticket_type.name} ({self.unique_code})"