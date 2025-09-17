from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegistrationSerializer,PasswordResetSerializer, ConfirmNewPasswordSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .receivers import password_reset_requested, user_registered

class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        saved_account = serializer.save()

        token  = default_token_generator.make_token(saved_account)
        
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
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"message": "Invalid activation link."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not hasattr(user, 'activation_token') or not user.activation_token.is_valid():
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
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        password_reset_requested.send(
                sender=self.__class__,
                user=user,
                token=token,
                uidb64=uidb64
            )
        
        return Response({"detail": "An email has been sent to reset your password."})
    

class ConfirmPasswordResetView(APIView):
    def post(self, request, uidb64, token):
        serializer = ConfirmNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                uidb64 = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uidb64)
            except(TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response({"message": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)
            
            if not hasattr(user, 'activation_token') or not user.activation_token.is_valid():
                user.activation_token.delete()
                return Response({"message": "Activation link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)
        
            if not default_token_generator.check_token(user, token):
                return Response({"message": "Activation link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)
            
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()
            user.activation_token.delete()
            return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)