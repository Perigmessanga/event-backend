import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

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
                subject="Votre code OTP EventManager",
                message=f"Votre code OTP est : {otp_code}",
                from_email=FROM_EMAIL,
                recipient_list=[user_data['email']],
                fail_silently=False,
            )

            return Response({"message": "OTP envoyé. Vérifiez votre email."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# LOGIN
# -------------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"error": "Email ou mot de passe incorrect"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Connexion réussie",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        })


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
        return Response({"error": "Email requis"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        otp_obj = OTPVerification.objects.get(email=email)
    except OTPVerification.DoesNotExist:
        return Response({"error": "Aucune demande d'inscription trouvée pour cet email"}, status=status.HTTP_404_NOT_FOUND)

    otp_code = str(random.randint(100000, 999999))
    otp_obj.otp_code = otp_code
    otp_obj.is_verified = False
    otp_obj.expires_at = timezone.now() + timedelta(minutes=5)
    otp_obj.save()

    send_mail(
        subject="Votre code OTP Award Dan",
        message=f"Votre nouveau code OTP est : {otp_code}",
        from_email=FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return Response({"message": "OTP renvoyé avec succès"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get("email")
    code = request.data.get("otp_code")

    try:
        otp_obj = OTPVerification.objects.get(email=email, otp_code=code, is_verified=False)
    except OTPVerification.DoesNotExist:
        return Response({"error": "OTP invalide ou expiré"}, status=status.HTTP_400_BAD_REQUEST)

    if timezone.now() > otp_obj.expires_at:
        return Response({"error": "OTP expiré"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = RegisterSerializer(data=otp_obj.pending_user_data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    otp_obj.is_verified = True
    otp_obj.save()

    return Response({
        "message": "Compte créé avec succès, vous pouvez maintenant vous connecter.",
        "user": UserSerializer(user).data
    }, status=status.HTTP_201_CREATED)


# -------------------------------
# CHANGE PASSWORD
# -------------------------------
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not old_password or not new_password or not confirm_password:
            return Response({"error": "Tous les champs sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({"error": "Ancien mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "Le nouveau mot de passe et la confirmation ne correspondent pas."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Mot de passe changé avec succès."}, status=status.HTTP_200_OK)


# -------------------------------
# LOGOUT
# -------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()  # nécessite d'activer la blacklist SimpleJWT
        except Exception:
            pass

        return Response({"message": "Déconnexion réussie."}, status=status.HTTP_200_OK)


# -------------------------------
# FORGOT PASSWORD (envoi OTP)
# -------------------------------
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Utilisateur inexistant."}, status=status.HTTP_404_NOT_FOUND)

        otp_code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)

        OTPVerification.objects.update_or_create(
            email=email,
            defaults={"otp_code": otp_code, "expires_at": expires_at, "is_verified": False, "pending_user_data": {}}
        )

        send_mail(
            subject="Réinitialisation de mot de passe",
            message=f"Votre code OTP pour réinitialiser le mot de passe est : {otp_code}",
            from_email=FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"message": "OTP envoyé par email."}, status=status.HTTP_200_OK)


# -------------------------------
# RESET PASSWORD (avec OTP)
# -------------------------------
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp_code = request.data.get("otp_code")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not all([email, otp_code, new_password, confirm_password]):
            return Response({"error": "Tous les champs sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "Le nouveau mot de passe et la confirmation ne correspondent pas."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj = OTPVerification.objects.get(email=email, otp_code=otp_code, is_verified=False)
        except OTPVerification.DoesNotExist:
            return Response({"error": "OTP invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() > otp_obj.expires_at:
            return Response({"error": "OTP expiré."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Utilisateur inexistant."}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()

        otp_obj.is_verified = True
        otp_obj.save()

        return Response({"message": "Mot de passe réinitialisé avec succès."}, status=status.HTTP_200_OK)