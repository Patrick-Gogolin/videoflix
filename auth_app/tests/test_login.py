from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User

class LoginAPITestCase(APITestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "securepassword123"
        self.user = User.objects.create_user(username=self.email, email=self.email, password=self.password, is_active=True)

    def perform_valid_login(self):
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

        return login_response,access_token, refresh_token

    def perform_invalid_login(self, email, password):
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
        logout_url = reverse('logout')
        logout_response = self.client.post(logout_url, HTTP_COOKIE=f'access_token={access_token}; refresh_token={refresh_token}')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(logout_response.cookies['access_token'].value, '')
        self.assertEqual(logout_response.cookies['refresh_token'].value, '')
        self.assertIn('Logout successful!', logout_response.data['detail'])

    def test_login_successful(self):
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
       self.perform_invalid_login(self.email, "wrongpassword")
    
    def test_login_nonexistent_user(self):
        self.perform_invalid_login("nonexistent@example.com", "somepassword")
    
    def test_login_inactive_user(self):
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
        _, access_token, refresh_token = self.perform_valid_login()

        self.perform_logout(access_token, refresh_token)
    
    def test_refresh_token_blacklisted(self):
        _, access_token, refresh_token = self.perform_valid_login()

        self.perform_logout(access_token, refresh_token)

        token_refresh_url = reverse('token_refresh')
        token_refresh_response = self.client.post(token_refresh_url, HTTP_COOKIE=f'refresh_token={refresh_token}')
        self.assertEqual(token_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Invalid refresh token.", token_refresh_response.data['detail'])
        #Hier muss geklärt werden wie das mit dem logout gemeint ist