from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core import mail
from auth_app.api.tasks import send_password_reset_email

class PasswordResetAPITestCase(APITestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "securepassword123"
        self.user = User.objects.create_user(username=self.email, email=self.email, password=self.password, is_active=True)
    
    def test_send_password_reset_mail_sucessful(self):
        url = reverse('password_reset')
        data = {
            "email": self.user.email
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        send_password_reset_email(self.user.pk, self.user.email)
        email = mail.outbox[0]
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reset your Password", email.subject)
        self.assertIn("test@example.com", email.to)
        self.assertIn("Click the link to reset your password", email.body)

    def test_send_password_reset_mail_not_existing_user(self):
        url = reverse('password_reset')
        data = {
            "email": "notexisting@test.de"
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("User with this email does not exist.", response.data['email'][0])
        self.assertEqual(len(mail.outbox), 0)