from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from auth_app.models import ActivationToken
from datetime import timedelta

class AccountActivationTestCase(APITestCase):
    def setUp(self):
        self.email = "inactive@example.com"
        self.password = "securepassword123"
        self.user = User.objects.create_user(username=self.email, email=self.email, password=self.password, is_active=False)
        self.activation_token = ActivationToken.objects.create(user=self.user)
    
    def test_account_activation_successful(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        url = reverse('activate', kwargs={"uidb64": uidb64, "token": token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_account_activation_invalid_token(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = "invalid-token"

        url = reverse('activate', kwargs={"uidb64": uidb64, "token": token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
    
    def test_account_activation_expired_token(self):
        self.user.activation_token.created_at = timezone.now() - timedelta(days=2)
        self.user.activation_token.save()

        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        url = reverse('activate', kwargs={"uidb64": uidb64, "token": token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Activation link is invalid or has expired.", response.data["message"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_account_activation_invalid_uid(self):
        uidb64 = "invalid-uid"
        token = default_token_generator.make_token(self.user)

        url = reverse('activate', kwargs={"uidb64": uidb64, "token": token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Invalid activation link.", response.data["message"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
    
    def test_account_activation_without_activation_token(self):
        self.user.activation_token.delete()

        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        url = reverse('activate', kwargs={"uidb64": uidb64, "token": token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Activation link is invalid or has expired.", response.data["message"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)