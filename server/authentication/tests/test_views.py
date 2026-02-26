from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


REGISTER_URL = '/api/auth/register/'

VALID_PAYLOAD = {
    'first_name': 'John',
    'last_name': 'Doe',
    'username': 'johndoe',
    'email': 'john@example.com',
    'password': 'securepassword123',
}


class RegisterViewSuccessTest(APITestCase):
    """Tests for successful POST /api/auth/register/ requests."""

    def setUp(self):
        self.response = self.client.post(REGISTER_URL, VALID_PAYLOAD, format='json')

    def test_returns_201(self):
        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)

    def test_response_contains_token(self):
        self.assertIn('token', self.response.data)
        self.assertTrue(self.response.data['token'])

    def test_response_user_has_first_name(self):
        self.assertEqual(self.response.data['user']['first_name'], 'John')

    def test_response_user_has_last_name(self):
        self.assertEqual(self.response.data['user']['last_name'], 'Doe')

    def test_response_user_has_username(self):
        self.assertEqual(self.response.data['user']['username'], 'johndoe')

    def test_user_record_stores_first_name(self):
        user = User.objects.get(username='johndoe')
        self.assertEqual(user.first_name, 'John')

    def test_user_record_stores_last_name(self):
        user = User.objects.get(username='johndoe')
        self.assertEqual(user.last_name, 'Doe')

    def test_user_record_stores_username(self):
        user = User.objects.get(username='johndoe')
        self.assertEqual(user.username, 'johndoe')


class RegisterViewMissingFieldsTest(APITestCase):
    """Tests that missing required fields return 400."""

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
    """Tests for duplicate registration attempts."""

    def test_duplicate_username_returns_400(self):
        self.client.post(REGISTER_URL, VALID_PAYLOAD, format='json')
        response = self.client.post(REGISTER_URL, VALID_PAYLOAD, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
