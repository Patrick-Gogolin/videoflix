from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
from django.core import mail
from auth_app.api.tasks import send_activation_email_task

class RegistrationAPITestCase(APITestCase):
    """
    Test case for the user registration API endpoint.

    Covers scenarios such as:
    - Successful registration
    - Registration with existing email
    - Registration with non-matching passwords
    - Missing required fields
    - Ensuring email is set as username
    """
    def setUp(self):
        """Set up a test user with inactive status and an existing email."""
        self.user = User.objects.create_user(
            username="inactive@example.com",
            email="inactive@example.com",
            password="securepassword123",
            is_active=False
        )

    def try_registration(self, email, password, confirmed_password):
        """
        Helper method to perform a registration request.

        Args:
            email (str): Email for the new user.
            password (str): Password for the new user.
            confirmed_password (str): Confirmation of the password.

        Returns:
            Response: The DRF response from the registration endpoint.
        """
        url = reverse('register')
        data = {
            "email": email,
            "password": password,
            "confirmed_password": confirmed_password
        }
        response = self.client.post(url, data, format="json")
        return response

    def test_registration_success(self):
        """Test successful registration of a new user and sending of activation email."""
        response = self.try_registration("newuser@example.com", "securepassword123", "securepassword123")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="newuser@example.com")
        self.assertFalse(user.is_active)
        self.assertTrue(hasattr(user, "activation_token"))
        self.assertTrue(user.activation_token.is_valid())
        
        send_activation_email_task(user.pk, user.email)
        email = mail.outbox[0]
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Confirm your email", email.subject)
        self.assertIn("newuser@example.com", email.to)
        self.assertIn("Click the link to activate", email.body)

    def test_registration_existing_user(self):
        """Test registration attempt with an email that already exists returns 400."""
        response = self.try_registration("inactive@example.com", "securepassword123", "securepassword123")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Email is already in use.", response.data["non_field_errors"])
        self.assertEqual(User.objects.filter(email="inactive@example.com").count(), 1)

    
    def test_registration_not_matching_passwords(self):
        """Test that registration fails if password and confirmed_password do not match."""
        response = self.try_registration("newuser@example.com", "securepassword12", "securepassword123")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        """Test that registration fails when required fields are missing."""
        self.assertIn("Passwords do not match.", response.data["non_field_errors"])
        self.assertEqual(User.objects.filter(email="inactive@example.com").count(), 1)
    
    def test_registration_missing_fields(self):
        """Test that registration fails when required fields are missing."""
        url = reverse('register')
        data = {}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.data["email"][0], "This field is required.")
        self.assertEqual(response.data["password"][0], "This field is required.")
        self.assertEqual(response.data["confirmed_password"][0], "This field is required.")
    
    def test_registration_email_set_to_username(self):
        """Test that the email is automatically set as the username upon registration."""
        response = self.try_registration("newuser@example.com", "securepassword123", "securepassword123")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="newuser@example.com")
        self.assertTrue(user.email == user.username)