from django.contrib import admin
from .models import Event, TicketType, Category

# Inline pour les tickets liés à l'événement
class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 1
    fields = ('name', 'price', 'quantity_total', 'quantity_sold', 'available_display')
    readonly_fields = ('available_display',)
    show_change_link = True

    # <-- bien indenté à l'intérieur de la classe
    def available_display(self, obj):
        return obj.available if obj.available is not None else 0
    available_display.short_description = "Available Tickets"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'status')
    inlines = [TicketTypeInline]

@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'available')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')