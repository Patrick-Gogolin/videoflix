from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User


class TokenRefreshAPITestCase(APITestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "securepassword123"
        self.user = User.objects.create_user(username=self.email, email=self.email, password=self.password, is_active=True)


    def test_token_refresh_successfull(self):
        login_url = reverse('token_obtain_pair')
        data =  {
            'email': self.email,
            'password': self.password
        }
        login_response = self.client.post(login_url, data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        refresh_token = login_response.cookies.get('refresh_token').value
        after_login_access_token = login_response.cookies.get('access_token').value
        self.assertIsNotNone(refresh_token)
        self.assertIsNotNone(after_login_access_token)

        token_refresh_url = reverse('token_refresh')
        token_refresh_response = self.client.post(token_refresh_url, HTTP_COOKIE=f'refresh_token={refresh_token}')
        after_token_refresh_access_token = token_refresh_response.cookies.get('access_token').value
        self.assertEqual(token_refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', token_refresh_response.cookies)
        self.assertNotEqual(after_login_access_token, after_token_refresh_access_token)
    
    def test_token_refresh_not_provided(self):
        token_refresh_url = reverse('token_refresh')
        token_refresh_response = self.client.post(token_refresh_url)
        self.assertEqual(token_refresh_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Refresh token not provided.", token_refresh_response.data["detail"])
    
    def test_token_refresh_invalid_token(self):
        token_refresh_url = reverse('token_refresh')
        token_refresh_response = self.client.post(token_refresh_url, HTTP_COOKIE='refresh_token=invalidtoken')
        self.assertEqual(token_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Invalid refresh token.", token_refresh_response.data["detail"])