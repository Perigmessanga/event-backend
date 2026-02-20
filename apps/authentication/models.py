from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
import random

class CustomUser(AbstractUser):
    """Custom User Model with additional fields for Event Management"""
    
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('organizer', 'Organizer'),
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^(\+\d{1,3})?[\d\s\-()]{6,}$',
                message='Phone number must be valid (6+ digits)',
                code='invalid_phone'
            )
        ]
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # Permet de bloquer un utilisateur
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        # Utilisation directe de la méthode
        return f"{self.full_name} ({self.email})"
    
    @property
    def full_name(self):
        """Retourne le nom complet ou le username si vide"""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def block(self):
        """Bloque l'utilisateur"""
        self.is_active = False
        self.save()

    def unblock(self):
        """Débloque l'utilisateur"""
        self.is_active = True
        self.save()


from django.conf import settings
from django.db import models

class OTP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps"  # <-- unique name
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

class OTPVerification(models.Model):
    email = models.EmailField(unique=True)
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    pending_user_data = models.JSONField(null=True, blank=True)  # Stocke les données temporaires

    
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)


