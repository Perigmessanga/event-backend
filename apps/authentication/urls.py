from . import views
from django.urls import path
from .views import RegisterView, LoginView, ProfileView
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("send-otp/", views.send_otp, name="send-otp"),
    path("verify-otp/", views.verify_otp, name="verify-otp"),
]
