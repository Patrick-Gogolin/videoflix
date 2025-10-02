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
    """
    Test case for the account activation API endpoint.

    This test suite covers the following scenarios:
    - Successful account activation
    - Activation with an invalid token
    - Activation with an invalid UID
            - Activation with an expired token
    - Activation attempt without an activation token
    - Reuse of an activation link (second attempt should fail)
    """
    def setUp(self):
        """Set up a test user with inactive status and a valid activation token."""
        self.email = "inactive@example.com"
        self.password = "securepassword123"
        self.user = User.objects.create_user(username=self.email, email=self.email, password=self.password, is_active=False)
        self.activation_token = ActivationToken.objects.create(user=self.user)

    def try_account_activation(self, uidb64=None, token=None):
        """
        Helper method to perform an account activation request.

        Args:
            uidb64 (str, optional): Base64-encoded user ID. Defaults to the test user's ID.
            token (str, optional): Activation token. Defaults to a freshly generated token.

        Returns:
            Response: The DRF response from the activation endpoint.
        """
        if uidb64 is None:
            uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        if token is None:
            token = default_token_generator.make_token(self.user)

        url = reverse('activate', kwargs={"uidb64": uidb64, "token": token})
        response = self.client.get(url)
        return response       

    def test_account_activation_successful(self):
        """Test that a valid activation link successfully activates the user account."""
        response = self.try_account_activation()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_account_activation_invalid_token(self):
        """Test that an invalid token returns a 400 Bad Request and does not activate the user."""
        response = self.try_account_activation(token='invalid-token')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_account_activation_invalid_uid(self):
        """Test that an invalid UID returns a 400 Bad Request and does not activate the user."""
        response = self.try_account_activation(uidb64='invalid-uid')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Activation link is invalid or has expired.", response.data["message"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
    
    def test_account_activation_expired_token(self):
        "Test that an expired activation token returns 400 and does not activate the user."""
        self.user.activation_token.created_at = timezone.now() - timedelta(days=2)
        self.user.activation_token.save()

        response = self.try_account_activation()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Activation link is invalid or has expired.", response.data["message"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
    
    def test_account_activation_without_activation_token(self):
        """Test that attempting activation without an existing token returns 400 and fails."""
        self.user.activation_token.delete()

        response = self.try_account_activation()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Activation link is invalid or has expired.", response.data["message"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
    
    def test_account_activation_link_cannot_be_reused(self):
        """
        Test that an activation link cannot be reused:
        - First request should activate the account successfully.
        - Second request with the same link should fail.
        """
        response_one = self.try_account_activation()
        self.assertEqual(response_one.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        response_two = self.try_account_activation()
        self.assertEqual(response_two.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Activation link is invalid or has expired.", response_two.data["message"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)