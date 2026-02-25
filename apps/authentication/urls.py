from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Register & OTP
    path('register/', views.RegisterView.as_view(), name='register'),
    path('send-otp/', views.send_otp, name='send-otp'),
    path('verify-otp/', views.verify_otp, name='verify-otp'),

    # Auth / JWT
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.LoginView.as_view(), name='token_refresh'),  # Si tu utilises simplejwt, sinon créer un TokenRefreshView

    # Profile
    path('me/', views.ProfileView.as_view(), name='profile'),

    # Password management
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
]