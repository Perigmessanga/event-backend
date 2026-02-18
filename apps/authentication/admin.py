from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, OTPVerification


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'is_email_verified', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone']
    list_filter = ['role', 'is_email_verified', 'is_phone_verified', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'role', 'profile_picture', 'bio', 'is_email_verified', 'is_phone_verified')
        }),
    )


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'verified', 'created_at']   # <-- seulement les vrais champs
    search_fields = ['user__email', 'user__phone']
    list_filter = ['verified', 'created_at']                    # <-- seulement les vrais champs
    ordering = ['-created_at']
    readonly_fields = ['created_at']
