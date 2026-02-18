# apps/users/utils.py
from django.utils import timezone
from datetime import timedelta
from .models import OTPVerification
from django.core.mail import send_mail
import random

def generate_otp_code():
    return f"{random.randint(100000, 999999)}"

def create_otp_for_user(user, otp_type='email'):
    """
    Crée un OTP pour l'utilisateur et l'envoie par mail (ou SMS si otp_type='phone')
    """
    otp_code = generate_otp_code()
    expires = timezone.now() + timedelta(minutes=10)

    otp_obj, created = OTPVerification.objects.update_or_create(
        user=user,
        otp_type=otp_type,
        defaults={
            'otp_code': otp_code,
            'is_verified': False,
            'attempts': 0,
            'expires_at': expires
        }
    )

    if otp_type == 'email':
        send_mail(
            subject="Votre code de vérification OTP",
            message=f"Bonjour {user.full_name},\n\nVotre code OTP est : {otp_code}\nIl expire dans 10 minutes.",
            from_email="no-reply@tikerama.com",
            recipient_list=[user.email],
        )
    # Pour SMS, intégrer Twilio ou autre ici

    return otp_obj
