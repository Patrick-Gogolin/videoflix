from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User

class LoginAPITestCase(APITestCase):
    """
    Test case for the login, logout, and token management API endpoints.

    This suite verifies:
    - Successful login with valid credentials
    - Login attempts with invalid or missing credentials
    - Behavior when logging in as an inactive user
    - Logout functionality and token invalidation
    - Token refresh flow with valid, missing, and invalid tokens
    """
    def setUp(self):
        """
        Set up a test user with valid credentials for login tests.
        """
        self.email = "test@example.com"
        self.password = "securepassword123"
        self.user = User.objects.create_user(username=self.email, email=self.email, password=self.password, is_active=True)

    def perform_valid_login(self):
        """
        Helper method to perform a valid login and return response with tokens.
        """
        login_url = reverse('token_obtain_pair')
        data =  {
            'email': self.email,
            'password': self.password
        }
        login_response = self.client.post(login_url, data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', login_response.cookies)
        self.assertIn('refresh_token', login_response.cookies)
        access_token = login_response.cookies.get('access_token').value
        refresh_token = login_response.cookies.get('refresh_token').value
        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)

        return login_response, access_token, refresh_token

    def perform_invalid_login(self, email, password):
        """
        Helper method to perform an invalid login attempt and verify error handling.
        """
        url = reverse('token_obtain_pair')
        data =  {
            'email': email,
            'password': password
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies)
        self.assertNotIn('refresh_token', response.cookies)
        self.assertIn("No active account found with the given credentials", response.data["non_field_errors"])
    
    def perform_logout(self, access_token, refresh_token):
        """
        Helper method to perform a logout and verify tokens are cleared.
        """
        logout_url = reverse('logout')
        logout_response = self.client.post(logout_url, HTTP_COOKIE=f'access_token={access_token}; refresh_token={refresh_token}')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(logout_response.cookies['access_token'].value, '')
        self.assertEqual(logout_response.cookies['refresh_token'].value, '')
        self.assertIn('Logout successful!', logout_response.data['detail'])

    def test_login_successful(self):
        """
        Test that a user can log in successfully with valid credentials.
        """
        response, _, _ = self.perform_valid_login()
        expected_data = {
            "detail": "Login successful",
            "user": {
                "id": self.user.id,
                "username": self.user.username,
            }
        }
        self.assertEqual(response.data, expected_data)
    
    def test_login_invalid_password(self):
        """
        Test login fails when the wrong password is provided.
        """
        self.perform_invalid_login(self.email, "wrongpassword")
    
    def test_login_nonexistent_user(self):
        """
        Test login fails for a non-existent user account.
        """
        self.perform_invalid_login("nonexistent@example.com", "somepassword")
    
    def test_login_inactive_user(self):
        """
        Test login fails for an inactive user account.
        """
        self.user.is_active = False
        self.user.save()
        url = reverse('token_obtain_pair')
        data =  {
            'email': self.email,
            'password': self.password
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access_token', response.cookies)
        self.assertNotIn('refresh_token', response.cookies)
        self.assertIn("No active account found with the given credentials", response.data["detail"])
    
    def test_login_missing_fields(self):
        """
        Test login fails when required fields (email and password) are missing.
        """
        url = reverse('token_obtain_pair')
        data =  {
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies)
        self.assertNotIn('refresh_token', response.cookies)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
        self.assertIn('This field is required.', response.data['email'])
        self.assertIn('This field is required.', response.data['password'])

    def test_logout_successful(self):
        """
        Test logout succeeds and clears tokens from cookies.
        """
        _, access_token, refresh_token = self.perform_valid_login()

        self.perform_logout(access_token, refresh_token)
    
    def test_logout_nonexistent_refresh_token(self):
        """
        Test logout fails if no refresh token is provided in cookies.
        """
        _, access_token, _ = self.perform_valid_login()

        logout_url = reverse('logout')
        logout_response = self.client.post(logout_url, HTTP_COOKIE=f'access_token={access_token}')
        self.assertEqual(logout_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual("Refresh token not provided.", logout_response.data['detail'])
    
    def test_refresh_token_blacklisted(self):
        """
        Test token refresh fails when using a blacklisted (logged out) refresh token.
        """
        _, access_token, blacklisted_refresh_token = self.perform_valid_login()

        self.perform_logout(access_token, blacklisted_refresh_token)

        token_refresh_url = reverse('token_refresh')
        token_refresh_response = self.client.post(token_refresh_url, HTTP_COOKIE=f'refresh_token={blacklisted_refresh_token}')
        self.assertEqual(token_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Invalid refresh token.", token_refresh_response.data['detail'])

    def test_token_refresh_successful(self):
        """
        Test token refresh succeeds with a valid refresh token and issues a new access token.
        """
        _, access_token, refresh_token = self.perform_valid_login()

        token_refresh_url = reverse('token_refresh')
        token_refresh_response = self.client.post(token_refresh_url, HTTP_COOKIE=f'refresh_token={refresh_token}')
        after_token_refresh_access_token = token_refresh_response.cookies.get('access_token').value
        self.assertEqual(token_refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', token_refresh_response.cookies)
        self.assertNotEqual(access_token, after_token_refresh_access_token)
    
    def test_token_refresh_not_provided(self):
        """
        Test token refresh fails when no refresh token is provided.
        """
        token_refresh_url = reverse('token_refresh')
        token_refresh_response = self.client.post(token_refresh_url)
        self.assertEqual(token_refresh_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Refresh token not provided.", token_refresh_response.data["detail"])
    
    def test_token_refresh_invalid_token(self):
        """
        Test token refresh fails when an invalid refresh token is provided.
        """
        token_refresh_url = reverse('token_refresh')
        token_refresh_response = self.client.post(token_refresh_url, HTTP_COOKIE='refresh_token=invalidtoken')
        self.assertEqual(token_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Invalid refresh token.", token_refresh_response.data["detail"])