from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.serializers import RegisterSerializer


REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"

VALID_PAYLOAD = {
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123",
}

# ---------------------------------------------------------------------------
# Canonical payload list — covers the most common injection techniques
# ---------------------------------------------------------------------------
SQL_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1--",
    "admin'--",
    "'; DROP TABLE auth_user; --",
    "' UNION SELECT username, password FROM auth_user--",
    '" OR "1"="1',
    "1; SELECT * FROM auth_user",
    "' OR 'x'='x",
    "' OR ''='",
    "') OR ('1'='1",
    "' OR 1=1#",
    "'; EXEC xp_cmdshell('dir'); --",
    "\x00",  # null byte
    "\\' OR 1=1--",  # escaped quote
]


# ---------------------------------------------------------------------------
# Serializer-level tests (no HTTP, fast)
# ---------------------------------------------------------------------------


class SqlInjectionUsernameSerializerTest(TestCase):
    """SQL payloads in username are rejected by the ^[a-z0-9]+$ validator."""

    def _is_invalid(self, username):
        s = RegisterSerializer(data={**VALID_PAYLOAD, "username": username})
        return not s.is_valid()

    def test_classic_or_injection(self):
        self.assertTrue(self._is_invalid("' OR '1'='1"))

    def test_comment_injection(self):
        self.assertTrue(self._is_invalid("admin'--"))

    def test_drop_table(self):
        self.assertTrue(self._is_invalid("'; DROP TABLE auth_user; --"))

    def test_union_select(self):
        self.assertTrue(
            self._is_invalid("' UNION SELECT username, password FROM auth_user--")
        )

    def test_double_quote_injection(self):
        self.assertTrue(self._is_invalid('" OR "1"="1'))

    def test_null_byte(self):
        self.assertTrue(self._is_invalid("\x00"))

    def test_all_payloads_rejected(self):
        for payload in SQL_PAYLOADS:
            with self.subTest(payload=payload):
                self.assertTrue(
                    self._is_invalid(payload),
                    f"Payload was not rejected by username validator: {payload!r}",
                )


class SqlInjectionEmailSerializerTest(TestCase):
    """SQL payloads in email are rejected by EmailField."""

    def _is_invalid(self, email):
        s = RegisterSerializer(data={**VALID_PAYLOAD, "email": email})
        return not s.is_valid()

    def test_all_payloads_rejected(self):
        for payload in SQL_PAYLOADS:
            with self.subTest(payload=payload):
                self.assertTrue(
                    self._is_invalid(payload),
                    f"Payload was not rejected by email validator: {payload!r}",
                )


class SqlInjectionNameSerializerTest(TestCase):
    """SQL payloads in first_name / last_name are rejected by ^[a-zA-Z\\s-]+$."""

    def _first_name_invalid(self, value):
        s = RegisterSerializer(data={**VALID_PAYLOAD, "first_name": value})
        return not s.is_valid()

    def _last_name_invalid(self, value):
        s = RegisterSerializer(data={**VALID_PAYLOAD, "last_name": value})
        return not s.is_valid()

    def test_all_payloads_rejected_in_first_name(self):
        for payload in SQL_PAYLOADS:
            with self.subTest(payload=payload):
                self.assertTrue(
                    self._first_name_invalid(payload),
                    f"Payload was not rejected by first_name validator: {payload!r}",
                )

    def test_all_payloads_rejected_in_last_name(self):
        for payload in SQL_PAYLOADS:
            with self.subTest(payload=payload):
                self.assertTrue(
                    self._last_name_invalid(payload),
                    f"Payload was not rejected by last_name validator: {payload!r}",
                )


class SqlInjectionErrorFieldPlacementTest(TestCase):
    """Validation errors are attached to the specific field, not non_field_errors."""

    def test_sql_in_username_error_is_on_username_field(self):
        s = RegisterSerializer(data={**VALID_PAYLOAD, "username": "admin'--"})
        s.is_valid()
        self.assertIn("username", s.errors)
        self.assertNotIn("non_field_errors", s.errors)

    def test_sql_in_first_name_error_is_on_first_name_field(self):
        s = RegisterSerializer(data={**VALID_PAYLOAD, "first_name": "' OR 1=1--"})
        s.is_valid()
        self.assertIn("first_name", s.errors)
        self.assertNotIn("non_field_errors", s.errors)

    def test_sql_in_email_error_is_on_email_field(self):
        s = RegisterSerializer(data={**VALID_PAYLOAD, "email": "' OR 1=1--"})
        s.is_valid()
        self.assertIn("email", s.errors)
        self.assertNotIn("non_field_errors", s.errors)


# ---------------------------------------------------------------------------
# API / endpoint-level tests
# ---------------------------------------------------------------------------


class SqlInjectionRegisterEndpointTest(APITestCase):
    """SQL payloads POSTed to /register/ must return 400, never 500."""

    def _post(self, data):
        return self.client.post(REGISTER_URL, data, format="json")

    def test_sql_in_username_returns_400_not_500(self):
        for payload in SQL_PAYLOADS:
            with self.subTest(payload=payload):
                r = self._post({**VALID_PAYLOAD, "username": payload})
                self.assertEqual(
                    r.status_code,
                    status.HTTP_400_BAD_REQUEST,
                    f"Expected 400 for username={payload!r}, got {r.status_code}",
                )

    def test_sql_in_email_returns_400_not_500(self):
        for payload in SQL_PAYLOADS:
            with self.subTest(payload=payload):
                r = self._post({**VALID_PAYLOAD, "email": payload})
                self.assertEqual(
                    r.status_code,
                    status.HTTP_400_BAD_REQUEST,
                    f"Expected 400 for email={payload!r}, got {r.status_code}",
                )

    def test_sql_in_first_name_returns_400_not_500(self):
        for payload in SQL_PAYLOADS:
            with self.subTest(payload=payload):
                r = self._post({**VALID_PAYLOAD, "first_name": payload})
                self.assertEqual(
                    r.status_code,
                    status.HTTP_400_BAD_REQUEST,
                    f"Expected 400 for first_name={payload!r}, got {r.status_code}",
                )

    def test_sql_in_last_name_returns_400_not_500(self):
        for payload in SQL_PAYLOADS:
            with self.subTest(payload=payload):
                r = self._post({**VALID_PAYLOAD, "last_name": payload})
                self.assertEqual(
                    r.status_code,
                    status.HTTP_400_BAD_REQUEST,
                    f"Expected 400 for last_name={payload!r}, got {r.status_code}",
                )

    def test_injection_does_not_create_user(self):
        self._post({**VALID_PAYLOAD, "username": "' OR '1'='1"})
        self.assertEqual(User.objects.count(), 0)


class SqlInjectionLoginEndpointTest(APITestCase):
    """
    SQL payloads at /login/ must return 400 or 401, never 500.

    The login endpoint has no format validation on username/password —
    authenticate() receives them and queries the DB via the ORM (parameterised).
    The result is simply None (no match), so the endpoint returns 401.
    """

    def setUp(self):
        User.objects.create_user(
            username="legituser",
            password="securepassword123",
        )

    def _login(self, username, password="securepassword123"):
        return self.client.post(
            LOGIN_URL,
            {"username": username, "password": password},
            format="json",
        )

    def test_sql_in_username_returns_401_not_500(self):
        for payload in SQL_PAYLOADS:
            with self.subTest(payload=payload):
                r = self._login(username=payload)
                self.assertIn(
                    r.status_code,
                    [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED],
                    f"Expected 400 or 401 for username={payload!r}, got {r.status_code}",
                )

    def test_sql_in_password_returns_401_not_500(self):
        for payload in SQL_PAYLOADS:
            with self.subTest(payload=payload):
                r = self._login(username="legituser", password=payload)
                self.assertIn(
                    r.status_code,
                    [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED,
                     status.HTTP_429_TOO_MANY_REQUESTS],
                    f"Expected 400, 401, or 429 for password={payload!r}, got {r.status_code}",
                )

    def test_classic_bypass_does_not_authenticate(self):
        """' OR '1'='1 must NOT log in as any user."""
        r = self._login(username="' OR '1'='1", password="' OR '1'='1")
        self.assertNotEqual(r.status_code, status.HTTP_200_OK)
        self.assertNotIn("tokens", r.data)

    def test_tautology_bypass_does_not_authenticate(self):
        r = self._login(username="' OR 1=1--", password="anything")
        self.assertNotEqual(r.status_code, status.HTTP_200_OK)
        self.assertNotIn("tokens", r.data)

    def test_comment_injection_does_not_bypass_password(self):
        """admin'-- must not log in without the real password."""
        r = self._login(username="legituser'--", password="wrongpassword")
        self.assertNotEqual(r.status_code, status.HTTP_200_OK)
        self.assertNotIn("tokens", r.data)


# ---------------------------------------------------------------------------
# Database integrity tests — verify the DB is undamaged after all attacks
# ---------------------------------------------------------------------------


class SqlInjectionDatabaseIntegrityTest(APITestCase):
    """After a barrage of injection attempts, the database must be intact."""

    def setUp(self):
        User.objects.create_user(username="safeuser", password="securepassword123")

    def _flood(self):
        for payload in SQL_PAYLOADS:
            self.client.post(
                REGISTER_URL, {**VALID_PAYLOAD, "username": payload}, format="json"
            )
            self.client.post(
                REGISTER_URL, {**VALID_PAYLOAD, "email": payload}, format="json"
            )
            self.client.post(
                LOGIN_URL, {"username": payload, "password": payload}, format="json"
            )

    def test_user_table_survives_injection_attempts(self):
        self._flood()
        # The legitimate user must still exist and be queryable
        self.assertTrue(User.objects.filter(username="safeuser").exists())

    def test_no_extra_users_created_by_injection(self):
        count_before = User.objects.count()
        self._flood()
        self.assertEqual(User.objects.count(), count_before)

    def test_legitimate_user_password_unchanged(self):
        self._flood()
        user = User.objects.get(username="safeuser")
        self.assertTrue(user.check_password("securepassword123"))
