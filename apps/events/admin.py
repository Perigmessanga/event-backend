from django.contrib import admin
from .models import Event
from .models import Event, Category


admin.site.register(Category)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'status', 'start_date', 'capacity', 'ticket_price', 'created_at']
    search_fields = ['title', 'location', 'organizer__email']
    list_filter = ['status', 'start_date', 'created_at']
    ordering = ['-start_date']
