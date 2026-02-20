# apps/authentication/views.py
import random
import json
from datetime import timedelta
from django.contrib.auth import authenticate


from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import OTPVerification
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()
FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "Blbla <noreply@tikerama.com>")

# -------------------------------
# REGISTER VIEW: demande OTP
# -------------------------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data

            # Générer OTP
            otp_code = str(random.randint(100000, 999999))

            # Stocker OTP et données utilisateur temporairement
            OTPVerification.objects.update_or_create(
                email=user_data['email'],
                defaults={
                    "otp_code": otp_code,
                    "expires_at": timezone.now() + timedelta(minutes=5),
                    "is_verified": False,
                    "pending_user_data": user_data
                }
            )

            # Envoyer OTP par email
            send_mail(
                subject="Votre code OTP Tikerama",
                message=f"Votre code OTP est : {otp_code}",
                from_email=FROM_EMAIL,
                recipient_list=[user_data['email']],
                fail_silently=False,
            )

            return Response({"message": "OTP envoyé. Vérifiez votre email."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------------------------------
# PROFILE VIEW
# -------------------------------
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

# -------------------------------
# OTP PUBLIC ENDPOINTS
# -------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    email = request.data.get("email")

    if not email:
        return Response(
            {"error": "Email requis"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        otp_obj = OTPVerification.objects.get(email=email)
    except OTPVerification.DoesNotExist:
        return Response(
            {"error": "Aucune demande d'inscription trouvée pour cet email"},
            status=status.HTTP_404_NOT_FOUND
        )

    # Générer nouveau code
    otp_code = str(random.randint(100000, 999999))

    otp_obj.otp_code = otp_code
    otp_obj.is_verified = False
    otp_obj.expires_at = timezone.now() + timedelta(minutes=5)
    otp_obj.save()

    # Envoi email
    send_mail(
        subject="Votre code OTP",
        message=f"Votre nouveau code OTP est : {otp_code}",
        from_email=FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return Response(
        {"message": "OTP renvoyé avec succès"},
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get("email")
    code = request.data.get("otp_code")

    try:
        # On récupère l'OTP non vérifié pour cet email
        otp_obj = OTPVerification.objects.get(email=email, otp_code=code, is_verified=False)
    except OTPVerification.DoesNotExist:
        return Response({"error": "OTP invalide ou expiré"}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifier si l'OTP est expiré
    if timezone.now() > otp_obj.expires_at:
        return Response({"error": "OTP expiré"}, status=status.HTTP_400_BAD_REQUEST)

    # Créer l'utilisateur seulement si OTP valide
    serializer = RegisterSerializer(data=otp_obj.pending_user_data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    # Marquer l'OTP comme utilisé
    otp_obj.is_verified = True
    otp_obj.save()

    return Response({
        "message": "Compte créé avec succès, vous pouvez maintenant vous connecter.",
        "user": UserSerializer(user).data
    }, status=status.HTTP_201_CREATED)

    from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)

        if user is None:
            return Response(
                {"error": "Email ou mot de passe incorrect"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Connexion réussie",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        })

