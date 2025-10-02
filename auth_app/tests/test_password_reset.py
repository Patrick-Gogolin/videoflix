from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from datetime import timedelta
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core import mail
from auth_app.models import ActivationToken
from auth_app.api.tasks import send_password_reset_email

class PasswordResetAPITestCase(APITestCase):
    """
    Test case for the Password Reset feature in the auth app.

    Scenarios covered:
    - Sending password reset emails
    - Password reset with a valid token
    - Error cases: invalid token, expired token, invalid UID
    - Password validation: missing fields, non-matching passwords
    - Token reuse prevention
    """ 
    def setUp(self):
        """
        Set up a test user and its associated ActivationToken.
        """
        self.email = "test@example.com"
        self.password = "securepassword123"
        self.user = User.objects.create_user(username=self.email, email=self.email, password=self.password, is_active=True)
        self.activation_token = ActivationToken.objects.create(user=self.user)

    def reset_confirm(self, uidb64=None, token=None, new_password="newsecurepassword123", confirm_password="newsecurepassword123"):
        """
        Helper method to perform a password reset confirm request.

        Args:
            uidb64 (str, optional): Base64-encoded user ID. Defaults to the test user's ID.
            token (str, optional): Password reset token. Defaults to a newly generated token.
            new_password (str): The new password to set.
            confirm_password (str): Confirmation of the new password.

        Returns:
            Response: The DRF response from the password reset confirm endpoint.
        """
        if uidb64 is None:
            uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        if token is None:
            token = default_token_generator.make_token(self.user)
        
        url = reverse('password_confirm', kwargs={'uidb64': uidb64, 'token': token})
        data = {"new_password": new_password, "confirm_password": confirm_password}
        response  = self.client.post(url, data, format='json')
        return response
    
    def test_send_password_reset_mail_sucessful(self):
        """
        Test that a password reset email is sent successfully for an existing user.
        """
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
        """
        Test that a request with a non-existent email returns 400 and no email is sent.
        """
        url = reverse('password_reset')
        data = {
            "email": "notexisting@test.de"
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("User with this email does not exist.", response.data['email'][0])
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_password_reset_mail_missing_fields(self):
        """
        Test that missing email field returns a 400 error.
        """
        url = reverse('password_reset')
        data = {}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("This field is required.", response.data['email'][0])
    
    def test_password_reset_confirm_successful(self):
        """
        Test a successful password reset confirm request.
        """
        response = self.reset_confirm()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual("Your Password has been successfully reset.", response.data['detail'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newsecurepassword123"))
    
    def test_password_reset_confirm_passwords_do_not_match(self):
        """
        Test that a reset with non-matching passwords fails with 400.
        """
        response = self.reset_confirm(new_password="foo", confirm_password="bar")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match.", response.data['non_field_errors'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))

    def test_password_reset_confirm_invalid_token(self):
        """
        Test that an invalid token results in a 400 response.
        """
        response = self.reset_confirm(token="invalid-token")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Activation link is invalid or has expired.", response.data['message'])
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("Test12345$"))
    
    def test_password_reset_confirm_invalid_uid(self):
        """
        Test that an invalid UID results in a 400 response.
        """
        response = self.reset_confirm(uidb64="invalid-uid")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Activation link is invalid or has expired.", response.data['message'])
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("Test12345$"))
    
    def test_password_reset_confirm_expired_token(self):
        """
        Test that an expired activation token results in a 400 response.
        """
        self.user.activation_token.created_at = timezone.now() - timedelta(days=2)
        self.user.activation_token.save()

        response = self.reset_confirm()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Activation link is invalid or has expired.", response.data['message'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))
    
    def test_password_reset_token_cannot_be_reused(self):
        """
        Test that a password reset token cannot be used more than once.
        """
        responseOne = self.reset_confirm()
        self.assertEqual(responseOne.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newsecurepassword123"))

        responseTwo = self.reset_confirm()
        self.assertEqual(responseTwo.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newsecurepassword123"))

    def test_password_reset_confirm_missing_fields(self):
        """
        Test that missing new_password or confirm_password fields result in 400.
        """
        response = self.reset_confirm(new_password=None, confirm_password=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)
        self.assertIn("confirm_password", response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))