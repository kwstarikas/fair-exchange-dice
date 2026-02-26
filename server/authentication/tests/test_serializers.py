from django.contrib.auth.models import User
from django.test import TestCase

from authentication.serializers import RegisterSerializer


VALID_DATA = {
    'first_name': 'John',
    'last_name': 'Doe',
    'username': 'johndoe',
    'email': 'john@example.com',
    'password': 'securepassword123',
}


class RegisterSerializerValidationTest(TestCase):
    """Tests for RegisterSerializer field validation."""

    def test_valid_data_passes(self):
        serializer = RegisterSerializer(data=VALID_DATA)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_first_name_required(self):
        data = {**VALID_DATA}
        del data['first_name']
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)

    def test_last_name_required(self):
        data = {**VALID_DATA}
        del data['last_name']
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('last_name', serializer.errors)

    def test_username_required(self):
        data = {**VALID_DATA}
        del data['username']
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_password_required(self):
        data = {**VALID_DATA}
        del data['password']
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_empty_first_name_invalid(self):
        serializer = RegisterSerializer(data={**VALID_DATA, 'first_name': ''})
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)

    def test_empty_last_name_invalid(self):
        serializer = RegisterSerializer(data={**VALID_DATA, 'last_name': ''})
        self.assertFalse(serializer.is_valid())
        self.assertIn('last_name', serializer.errors)

    def test_weak_password_rejected(self):
        serializer = RegisterSerializer(data={**VALID_DATA, 'password': 'password'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='johndoe', password='irrelevant99')
        serializer = RegisterSerializer(data=VALID_DATA)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)


class RegisterSerializerCreateTest(TestCase):
    """Tests that RegisterSerializer.create() persists all fields correctly."""

    def setUp(self):
        serializer = RegisterSerializer(data=VALID_DATA)
        serializer.is_valid(raise_exception=True)
        self.user = serializer.save()

    def test_first_name_saved(self):
        self.assertEqual(self.user.first_name, 'John')

    def test_last_name_saved(self):
        self.assertEqual(self.user.last_name, 'Doe')

    def test_username_saved(self):
        self.assertEqual(self.user.username, 'johndoe')

    def test_password_is_hashed(self):
        self.assertTrue(self.user.check_password('securepassword123'))
        self.assertNotEqual(self.user.password, 'securepassword123')
