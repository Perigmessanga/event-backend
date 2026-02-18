from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CustomUser
from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser, OTPVerification
from django.utils import timezone
# apps/authentication/views.py
import json                     # Pour json.loads()
from datetime import timedelta   # Pour définir l'expiration OTP
from django.utils import timezone
from django.http import JsonResponse  # Pour renvoyer des réponses JSON

from twilio.rest import Client   # Pour envoyer des SMS
from .models import CustomUser, OTPVerification
import random
# apps/auth/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .utils import generate_otp, verify_otp

FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "Blbla <noreply@tikerama.com>")

class SendOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        
        generate_otp(user)
        return Response({"message": "OTP envoyé"}, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        
        if verify_otp(user, code):
            return Response({"message": "OTP validé"}, status=status.HTTP_200_OK)
        return Response({"error": "OTP invalide ou expiré"}, status=status.HTTP_400_BAD_REQUEST)


User = get_user_model()


# =========================================
# REGISTER VIEW
# =========================================

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # Récupère l'utilisateur créé dans le serializer
            print("Utilisateur créé :", user)
            # ⚡ ENVOI DE L'OTP
            send_otp_to_user(user)
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'User registered successfully. OTP envoyé.',
                'user': UserSerializer(user).data,
                # 'refresh': str(refresh),
                # 'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def send_otp_to_user(user):
    """Crée un OTP et l'envoie par email ou SMS"""
    otp_code = str(random.randint(100000, 999999))
    OTPVerification.objects.update_or_create(
    user=user,
    defaults={
        "code": otp_code,
        "verified": False,
        "created_at": timezone.now()
    }
)


    # ⚡ Email
    from django.core.mail import send_mail
    send_mail(
        subject="Votre code OTP",
        message=f"Votre code OTP est : {otp_code}",
        from_email=FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )

    # ⚡ SMS avec Twilio (optionnel)
    # client = Client(TWILIO_SID, TWILIO_AUTH)
    # client.messages.create(
    #     body=f"Votre code OTP est : {otp_code}",
    #     from_=TWILIO_PHONE,
    #     to=user.phone
    # )



# =========================================
# LOGIN VIEW
# =========================================
class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Authenticate user with email and password, return JWT tokens
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================================
# PROFILE / ME VIEW
# =========================================
class ProfileView(APIView):
    """
    GET /api/v1/auth/me/
    Get authenticated user's profile
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_data = UserSerializer(request.user).data
        return Response(user_data, status=status.HTTP_200_OK)

    def put(self, request):
        """Update user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



TWILIO_SID = "TON_SID"
TWILIO_AUTH = "TON_AUTH_TOKEN"
TWILIO_PHONE = "+123456789"

@api_view(['POST'])
def send_otp(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email_or_phone = data.get("email") or data.get("phone")
        user = CustomUser.objects.filter(email=email_or_phone).first()
        if not user:
            return JsonResponse({"error": "Utilisateur non trouvé"}, status=404)

        otp_code = str(random.randint(100000, 999999))
        OTPVerification.objects.update_or_create(
            user=user,
            otp_type="email",
            defaults={
                "otp_code": otp_code,
                "expires_at": timezone.now() + timedelta(minutes=5),
                "is_verified": False
            }
        )

        # Envoi par email ou SMS
        client = Client("TWILIO_SID", "TWILIO_AUTH_TOKEN")
        client.messages.create(
            body=f"Votre code OTP est : {otp_code}",
            from_="+1234567890",
            to=user.phone
        )

        return JsonResponse({"message": "OTP envoyé"})

@api_view(['POST'])
def verify_otp(request):
    email = request.data.get('email')
    code = request.data.get('otp_code')  # tu peux garder 'otp_code' côté frontend

    try:
        user = CustomUser.objects.get(email=email)
        # Utiliser les nouveaux champs 'code' et 'verified'
        otp_obj = OTPVerification.objects.get(user=user, code=code, verified=False)

        # Vérifier si l'OTP est expiré (tu peux créer expires_at si tu veux, sinon juste vérifier created_at)
        # Par exemple, 5 minutes de validité
        expiration_time = otp_obj.created_at + timezone.timedelta(minutes=5)
        if timezone.now() > expiration_time:
            return Response({'error': 'OTP expiré'}, status=status.HTTP_400_BAD_REQUEST)

        # Marquer l'OTP comme vérifié
        otp_obj.verified = True
        otp_obj.save()

        # Marquer l'email comme vérifié
        user.is_email_verified = True
        user.save()

        return Response({'message': 'OTP validé, vous pouvez vous connecter'}, status=status.HTTP_200_OK)

    except CustomUser.DoesNotExist:
        return Response({'error': 'Utilisateur introuvable'}, status=status.HTTP_404_NOT_FOUND)
    except OTPVerification.DoesNotExist:
        return Response({'error': 'OTP invalide'}, status=status.HTTP_400_BAD_REQUEST)

