from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'status', 'payment_method', 'transaction_id', 'created_at']
    search_fields = ['order__user__email', 'transaction_id']
    list_filter = ['status', 'payment_method', 'created_at']
    ordering = ['-created_at']
