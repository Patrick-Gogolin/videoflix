from django.urls import path
from .views import RegistrationView, ActivateAccountView, SendPasswortResetMail, ConfirmPasswordResetView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
    path('password_reset/', SendPasswortResetMail.as_view(), name='password_reset'),
    path('password_confirm/<uidb64>/<token>/', ConfirmPasswordResetView.as_view(), name='password_confirm'),
]