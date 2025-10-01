from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegistrationSerializer, PasswordResetSerializer, ConfirmNewPasswordSerializer, CustomTokenObtainPairSerializer
from .receivers import password_reset_requested, user_registered

class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        saved_account = serializer.save()

        token = default_token_generator.make_token(saved_account)

        user_registered.send(self.__class__, user=saved_account)

        data = {
            "user": {
                "id": saved_account.pk,
                "email": saved_account.email,
            },
            "token": token
        }

        return Response(data, status=status.HTTP_201_CREATED)

class ActivateAccountView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"message": "Invalid activation link."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not hasattr(user, 'activation_token'):
            return Response({"message": "Activation link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.activation_token.is_valid():
            user.activation_token.delete()
            return Response({"message": "Activation link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"message": "Activation link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        user.activation_token.delete()

        return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)

class SendPasswortResetMail(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        password_reset_requested.send(
            sender=self.__class__,
            user=user,
        )

        return Response({"detail": "An email has been sent to reset your password."})

class ConfirmPasswordResetView(APIView):
    def post(self, request, uidb64, token):
        serializer = ConfirmNewPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            uidb64 = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uidb64)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"message": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)

        if not hasattr(user, 'activation_token') or not user.activation_token.is_valid():
            if hasattr(user, 'activation_token'):
                user.activation_token.delete()
            return Response({"message": "Activation link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"message": "Activation link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)

        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        if hasattr(user, 'activation_token'):
            user.activation_token.delete()

        return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=request.data['email'])

        refresh = serializer.validated_data['refresh']
        access = serializer.validated_data['access']

        response = Response({
            "detail": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username
            }
        })

        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            samesite='Lax',
            secure=True
        )

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            samesite='Lax',
            secure=True
        )

        return response

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response({"detail": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data={'refresh': refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        
        access_token = serializer.validated_data.get('access')

        response = Response({
        "detail": "Token refreshed",
        "access": access_token
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            samesite='Lax',
            secure=True
        )

        return response

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response({"detail": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        
        response = Response({"detail": "Logout successful! All Tokens will be deleted. Refresh token is now invalid."}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response