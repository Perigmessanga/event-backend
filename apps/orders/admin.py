from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'event', 'quantity', 'total_price', 'status', 'created_at']
    search_fields = ['user__email', 'event__title']
    list_filter = ['status', 'created_at']
    ordering = ['-created_at']
