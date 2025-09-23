from django.urls import path
from .views import RegistrationView, ActivateAccountView, SendPasswortResetMail, ConfirmPasswordResetView, LoginView, CookieTokenRefreshView, LogoutView

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),
    path('password_reset/', SendPasswortResetMail.as_view(), name='password_reset'),
    path('password_confirm/<uidb64>/<token>/', ConfirmPasswordResetView.as_view(), name='password_confirm'),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout')
]