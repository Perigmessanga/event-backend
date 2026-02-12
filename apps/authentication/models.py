from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

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


class OTPVerification(models.Model):
    """OTP verification for phone and email"""
    
    OTP_TYPE_CHOICES = [
        ('phone', 'Phone'),
        ('email', 'Email'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='otp_verification')
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=10, choices=OTP_TYPE_CHOICES)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'otp_verification'
    
    def __str__(self):
        return f"OTP for {self.user.email} ({self.otp_type})"
