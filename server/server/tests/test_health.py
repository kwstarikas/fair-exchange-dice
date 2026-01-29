from rest_framework.test import APITestCase
from rest_framework import status


class HealthCheckTest(APITestCase):
    """Test that the API is reachable."""

    def test_admin_page_loads(self):
        """Test that admin login page is accessible."""
        response = self.client.get('/admin/login/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_docs_loads(self):
        """Test that Swagger documentation is accessible."""
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_openapi_schema_loads(self):
        """Test that OpenAPI schema is accessible."""
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
