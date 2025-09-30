from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
from django.core import mail
from auth_app.api.tasks import send_activation_email_task

class RegistrationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="inactive@example.com",
            email="inactive@example.com",
            password="securepassword123",
            is_active=False
        )

    def test_registration_success(self):
        url = reverse('register')
        data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "confirmed_password": "securepassword123"
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


        user = User.objects.get(email="newuser@example.com")
        self.assertFalse(user.is_active)
        self.assertTrue(hasattr(user, "activation_token"))
        self.assertTrue(user.activation_token.is_valid())
        
        send_activation_email_task(user.pk, user.email)
        email = mail.outbox[0]
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Confirm your email", email.subject)
        self.assertIn("Confirm your email", email.subject)
        self.assertIn("newuser@example.com", email.to)
        self.assertIn("Click the link to activate", email.body)

    def test_registration_existing_user(self):
        url = reverse('register')
        data = {
            "email": "inactive@example.com",
            "password": "securepassword123",
            "confirmed_password": "securepassword123"
        }
        
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Email is already in use.", response.data["non_field_errors"])
        self.assertEqual(User.objects.filter(email="inactive@example.com").count(), 1)
    
    def test_registration_not_matching_passwords(self):
        url = reverse('register')
        data = {
            "email": "newuser@example.com",
            "password": "securepassword12",
            "confirmed_password": "securepassword123"
        }
        
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match.", response.data["non_field_errors"])
        self.assertEqual(User.objects.filter(email="inactive@example.com").count(), 1)
    
    def test_registration_missing_fields(self):
        url = reverse('register')
        data = {}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.data["email"][0], "This field is required.")
        self.assertEqual(response.data["password"][0], "This field is required.")
        self.assertEqual(response.data["confirmed_password"][0], "This field is required.")
    
    def test_registration_email_set_to_username(self):
        url = reverse('register')
        data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "confirmed_password": "securepassword123"
        }
        
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="newuser@example.com")
        self.assertTrue(user.email == user.username)
