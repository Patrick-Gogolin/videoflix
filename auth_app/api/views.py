from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegistrationSerializer, PasswordResetSerializer, ConfirmNewPasswordSerializer, CustomTokenObtainPairSerializer
from .receivers import password_reset_requested, user_registered

class RegistrationView(APIView):
    """
    Registers a new user.

    Permissions: AllowAny

    - Validates input
    - Creates inactive user
    - Generates activation token
    - Sends activation email via `user_registered` signal
    """
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
    """
    API view to activate a user account via an activation link.

    GET Parameters:
        uidb64 (str): Base64-encoded user ID.
        token (str): Activation token generated for the user.

    Workflow:
    1. Decode the user ID from `uidb64` and retrieve the User object.
    2. Check that the user has a valid associated activation token.
    3. Verify the token with Django's default_token_generator.
    4. If all checks pass, activate the user's account (`is_active = True`) and delete the token.
    5. Return a success response if activation is successful, otherwise return an error.

    Responses:
        200 OK: Account successfully activated.
        400 Bad Request: Activation link is invalid or expired.
    """
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"message": "Activation link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)
        
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
    """
    APIView to initiate a password reset request.

    POST Parameters:
    - email (str): The email of the user requesting a password reset.

    Workflow:
    1. Validate the input email using PasswordResetSerializer.
    2. Save the serializer to create or retrieve an activation token for the user.
    3. Trigger the `password_reset_requested` signal, passing the user as sender.
    4. Send a response indicating that a password reset email has been sent.

    Permissions:
    - AllowAny: No authentication required to request a password reset.

    Responses:
    200 OK: Password reset email successfully triggered.
    400 Bad Request: Invalid email or serializer validation failed.
    """
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
    """
    APIView to confirm a password reset using a UID and token.

    POST Parameters:
    - new_password (str): The new password.
    - confirm_password (str): Confirmation of the new password.

    Workflow:
    1. Validate the new password and confirmation using ConfirmNewPasswordSerializer.
    2. Decode the uidb64 to retrieve the user ID and fetch the user.
    3. Check if the user has a valid activation token.
    4. Verify the provided token using Django's default_token_generator.
    5. Set the new password and save the user.
    6. Delete the activation token to prevent reuse.
    7. Return a success response if all validations pass.

    Permissions:
    - Implicitly accessible to users with the password reset link; no login required.

    Responses:
    200 OK: Password successfully reset.
    400 Bad Request: Invalid token, expired link, or serializer validation failed.
    """
    def post(self, request, uidb64, token):
        serializer = ConfirmNewPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            uidb64 = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uidb64)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"message": "Activation link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)

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
    """
    APIView for user login using JWT tokens.

    OST Parameters:
    - email (str): User's email.
    - password (str): User's password.

    Workflow:
    1. Validate credentials using CustomTokenObtainPairSerializer.
    2. Retrieve the user instance by email.
    3. Obtain JWT access and refresh tokens from the serializer.
    4. Return a response confirming successful login with user info.
    5. Set the access and refresh tokens as HttpOnly cookies for secure storage.

    Permissions:
    - Allow any user to access this endpoint (no authentication required).

    Responses:
    200 OK: Login successful with user info in the response.
    400 Bad Request: Invalid credentials or serializer validation failed.
    """
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
    """
    APIView to refresh JWT access tokens using a refresh token stored in cookies.

    POST Parameters:
    - None in body. The refresh token is read from the 'refresh_token' cookie.

    Workflow:
    1. Retrieve the refresh token from the request cookies.
    2. If missing, return 400 Bad Request.
    3. Validate the refresh token using the TokenRefreshView serializer.
    4. If invalid, return 401 Unauthorized.
    5. Generate a new access token.
    6. Return a response confirming the token refresh.
    7. Set the new access token as an HttpOnly cookie for secure storage.

    Permissions:
    - Accessible without authentication (AllowAny).

    Responses:
    200 OK: Access token successfully refreshed.
    400 Bad Request: Refresh token not provided.
    401 Unauthorized: Refresh token is invalid or expired.
    """
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
    """
    APIView to log out a user by blacklisting their refresh token and removing JWT cookies.

    POST Parameters:
    - None in body. The refresh token is read from the 'refresh_token' cookie.

    Workflow:
    1. Retrieve the refresh token from the request cookies.
    2. If missing, return 400 Bad Request.
    3. Attempt to blacklist the refresh token using the RefreshToken class.
    4. If invalid, return 400 Bad Request.
    5. Delete the access and refresh token cookies from the client.
    6. Return a 200 OK response confirming logout.

    Permissions:
    - Requires authentication (IsAuthenticated).

    Responses:
    200 OK: Logout successful, refresh token invalidated.
    400 Bad Request: Refresh token missing or invalid.
    """
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