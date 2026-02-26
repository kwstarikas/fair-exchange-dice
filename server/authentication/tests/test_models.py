from django.contrib.auth.models import User
from django.test import TestCase


class UserRegistrationFieldsTest(TestCase):
    """Tests that the User model correctly stores registration fields."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='securepassword123',
            first_name='John',
            last_name='Doe',
        )

    def test_first_name_is_stored(self):
        user = User.objects.get(username='johndoe')
        self.assertEqual(user.first_name, 'John')

    def test_last_name_is_stored(self):
        user = User.objects.get(username='johndoe')
        self.assertEqual(user.last_name, 'Doe')

    def test_username_is_stored(self):
        user = User.objects.get(username='johndoe')
        self.assertEqual(user.username, 'johndoe')

    def test_email_is_stored(self):
        user = User.objects.get(username='johndoe')
        self.assertEqual(user.email, 'john@example.com')

    def test_all_four_fields_persisted_together(self):
        user = User.objects.get(username='johndoe')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.username, 'johndoe')
        self.assertTrue(user.check_password('securepassword123'))
