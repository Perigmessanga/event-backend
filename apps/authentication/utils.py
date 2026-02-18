# apps/auth/utils.py
import random
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from .models import OTP

def generate_otp(user):
    code = f"{random.randint(100000, 999999)}"  # 6 chiffres
    expires_at = timezone.now() + timedelta(minutes=5)
    
    otp = OTP.objects.create(user=user, code=code, expires_at=expires_at)
    
    # Envoi par email
    send_mail(
        subject="Votre code OTP",
        message=f"Votre code OTP est {code}. Il expire dans 5 minutes.",
        from_email="no-reply@monapp.com",
        recipient_list=[user.email],
    )
    
    return otp
# apps/auth/utils.py
def verify_otp(user, code):
    try:
        otp = OTP.objects.filter(user=user, code=code, is_used=False).latest('created_at')
    except OTP.DoesNotExist:
        return False
    
    if otp.is_valid():
        otp.is_used = True
        otp.save()
        return True
    return False
