import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestHealthCheck:
    """Test that the API is reachable."""

    def test_root_endpoint(self):
        """Test that root endpoint returns hello world."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello": "World"}

    def test_items_endpoint(self):
        """Test that items endpoint works with path parameter."""
        response = client.get("/items/42")
        assert response.status_code == 200
        assert response.json()["item_id"] == 42

    def test_items_endpoint_with_query(self):
        """Test that items endpoint works with query parameter."""
        response = client.get("/items/1?q=test")
        assert response.status_code == 200
        assert response.json() == {"item_id": 1, "q": "test"}

    def test_docs_endpoint(self):
        """Test that Swagger docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
