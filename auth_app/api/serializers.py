from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from ..models import ActivationToken


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Validates password confirmation and ensures email uniqueness.
    Creates a new inactive user with an associated activation token.
    """
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'confirmed_password']
        extra_kwargs = {
            'email': {
                'required': True
            },
            'password': {
                'write_only': True
            },
            'username': {
                'required': False
            }
        }

    def validate(self, data):
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError("Passwords do not match.")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email is already in use.")
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False
        )
        ActivationToken.objects.create(user=user)
        return user

class PasswordResetSerializer(serializers.ModelSerializer):
    """
    Serializer for requesting a password reset.

    Validates that the provided email exists and
    creates or retrieves an activation token for the user.
    """
    class Meta:
        model = User

        fields = ['email']
        extra_kwargs =  {
            'email': {
                'required':True
            }
        }

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
        
    def create(self, validated_data):
        user = User.objects.get(email=validated_data['email'])
        ActivationToken.objects.get_or_create(user=user)
        return user

class ConfirmNewPasswordSerializer(serializers.Serializer):
    """
    Serializer for confirming a new password.

    Ensures that 'new_password' and 'confirm_password' match.
    """
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer for obtaining JWT tokens using email and password.

    Overrides the default TokenObtainPairSerializer to:
    - Use 'email' instead of 'username' for authentication.
    - Validate that the email exists and the password is correct.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "username" in self.fields:
            self.fields.pop("username")

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try: 
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No active account found with the given credentials")
        
        if not user.check_password(password):
            raise serializers.ValidationError("No active account found with the given credentials")

        data = super().validate({"username": user.username, "password": password})
        return data