from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


REGISTER_URL = '/api/auth/register/'
LOGIN_URL = '/api/auth/login/'
LOGOUT_URL = '/api/auth/logout/'
ME_URL = '/api/auth/me/'
TOKEN_REFRESH_URL = '/api/auth/token/refresh/'

VALID_PAYLOAD = {
    'first_name': 'John',
    'last_name': 'Doe',
    'username': 'johndoe',
    'email': 'john@example.com',
    'password': 'securepassword123',
}


def register(client, payload=None):
    return client.post(REGISTER_URL, payload or VALID_PAYLOAD, format='json')


def get_tokens(client, payload=None):
    response = register(client, payload)
    return {
        'access': response.cookies['access_token'].value,
        'refresh': response.cookies['refresh_token'].value,
    }


def auth(token):
    """Return credentials dict for client.credentials()."""
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

class RegisterViewSuccessTest(APITestCase):

    def setUp(self):
        self.response = register(self.client)

    def test_returns_201(self):
        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)

    def test_response_has_access_token(self):
        self.assertIn('access_token', self.response.cookies)
        self.assertTrue(self.response.cookies['access_token'].value)

    def test_response_has_refresh_token(self):
        self.assertIn('refresh_token', self.response.cookies)
        self.assertTrue(self.response.cookies['refresh_token'].value)

    def test_access_token_is_usable(self):
        access = self.response.cookies['access_token'].value
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        me = self.client.get(ME_URL)
        self.assertEqual(me.status_code, status.HTTP_200_OK)

    def test_response_user_has_first_name(self):
        self.assertEqual(self.response.data['user']['first_name'], 'John')

    def test_response_user_has_last_name(self):
        self.assertEqual(self.response.data['user']['last_name'], 'Doe')

    def test_response_user_has_username(self):
        self.assertEqual(self.response.data['user']['username'], 'johndoe')

    def test_user_record_stores_first_name(self):
        self.assertEqual(User.objects.get(username='johndoe').first_name, 'John')

    def test_user_record_stores_last_name(self):
        self.assertEqual(User.objects.get(username='johndoe').last_name, 'Doe')


class RegisterViewMissingFieldsTest(APITestCase):

    def _post(self, data):
        return self.client.post(REGISTER_URL, data, format='json')

    def test_missing_first_name_returns_400(self):
        data = {**VALID_PAYLOAD}
        del data['first_name']
        self.assertEqual(self._post(data).status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_last_name_returns_400(self):
        data = {**VALID_PAYLOAD}
        del data['last_name']
        self.assertEqual(self._post(data).status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_username_returns_400(self):
        data = {**VALID_PAYLOAD}
        del data['username']
        self.assertEqual(self._post(data).status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_returns_400(self):
        data = {**VALID_PAYLOAD}
        del data['password']
        self.assertEqual(self._post(data).status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_first_name_returns_400(self):
        self.assertEqual(
            self._post({**VALID_PAYLOAD, 'first_name': ''}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_empty_last_name_returns_400(self):
        self.assertEqual(
            self._post({**VALID_PAYLOAD, 'last_name': ''}).status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class RegisterViewDuplicateTest(APITestCase):

    def test_duplicate_username_returns_400(self):
        register(self.client)
        response = register(self.client)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTest(APITestCase):

    def setUp(self):
        register(self.client)
        self.client.credentials()  # clear auth

    def _login(self, username='johndoe', password='securepassword123'):
        return self.client.post(
            LOGIN_URL,
            {'username': username, 'password': password},
            format='json',
        )

    def test_valid_credentials_return_200(self):
        self.assertEqual(self._login().status_code, status.HTTP_200_OK)

    def test_response_has_access_token(self):
        response = self._login()
        self.assertIn('access_token', response.cookies)
        self.assertTrue(response.cookies['access_token'].value)

    def test_response_has_refresh_token(self):
        response = self._login()
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['refresh_token'].value)

    def test_access_token_is_usable(self):
        tokens = {'access': self._login().cookies['access_token'].value}
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_200_OK)

    def test_wrong_password_returns_401(self):
        self.assertEqual(self._login(password='wrongpassword').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_username_returns_401(self):
        self.assertEqual(self._login(username='nobody').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_password_returns_400(self):
        response = self.client.post(LOGIN_URL, {'username': 'johndoe'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_username_returns_400(self):
        response = self.client.post(LOGIN_URL, {'password': 'securepassword123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MeViewTest(APITestCase):

    def setUp(self):
        self.tokens = get_tokens(self.client)
        self.client.credentials()

    def test_with_valid_token_returns_200(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_200_OK)

    def test_returns_correct_username(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.assertEqual(self.client.get(ME_URL).data['username'], 'johndoe')

    def test_without_token_returns_401(self):
        self.client.cookies.clear()
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_with_invalid_token_returns_401(self):
        self.client.cookies.clear()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer notavalidtoken')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_with_wrong_scheme_returns_401(self):
        self.client.cookies.clear()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.tokens["access"]}')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutViewTest(APITestCase):

    def setUp(self):
        self.tokens = get_tokens(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')

    def test_logout_returns_200(self):
        response = self.client.post(LOGOUT_URL, {'refresh': self.tokens['refresh']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_token_rejected_after_logout(self):
        self.client.post(LOGOUT_URL, {'refresh': self.tokens['refresh']}, format='json')
        # The same access token should now be blacklisted
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_rejected_after_logout(self):
        self.client.post(LOGOUT_URL, {'refresh': self.tokens['refresh']}, format='json')
        self.client.credentials()  # clear access token
        response = self.client.post(
            TOKEN_REFRESH_URL,
            {'refresh': self.tokens['refresh']},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token_still_returns_200(self):
        # Graceful: missing refresh body should not crash the endpoint
        response = self.client.post(LOGOUT_URL, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_requires_authentication(self):
        self.client.credentials()
        self.client.cookies.clear()
        response = self.client.post(LOGOUT_URL, {'refresh': self.tokens['refresh']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    # ---------------------------------------------------------------------------
    # Token refresh
    # ---------------------------------------------------------------------------


class TokenRefreshViewTest(APITestCase):

    def setUp(self):
        self.tokens = get_tokens(self.client)
        self.client.credentials()

    def test_valid_refresh_returns_200(self):
        response = self.client.post(
            TOKEN_REFRESH_URL, {'refresh': self.tokens['refresh']}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_contains_new_access_token(self):
        response = self.client.post(
            TOKEN_REFRESH_URL, {'refresh': self.tokens['refresh']}, format='json'
        )
        self.assertIn('access', response.data)

    def test_new_access_token_is_usable(self):
        response = self.client.post(
            TOKEN_REFRESH_URL, {'refresh': self.tokens['refresh']}, format='json'
        )
        new_access = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access}')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_200_OK)

    def test_invalid_refresh_returns_401(self):
        self.client.cookies.clear()
        response = self.client.post(
            TOKEN_REFRESH_URL, {'refresh': 'notavalidtoken'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_refresh_returns_400(self):
        self.client.cookies.clear()
        response = self.client.post(TOKEN_REFRESH_URL, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
