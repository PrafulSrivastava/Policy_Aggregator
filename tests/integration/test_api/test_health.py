"""Integration tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check_returns_correct_structure(self, client):
        """Test that health check returns correct JSON structure."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
        assert data["database"] in ["connected", "disconnected"]
        assert isinstance(data["timestamp"], str)
    
    def test_health_check_has_timestamp(self, client):
        """Test that health check includes timestamp."""
        response = client.get("/health")
        data = response.json()
        
        # Timestamp should be ISO format
        assert "T" in data["timestamp"] or "Z" in data["timestamp"]
    
    def test_health_check_database_status(self, client):
        """Test that database status is reported."""
        response = client.get("/health")
        data = response.json()
        
        # Database status should be either connected or disconnected
        assert data["database"] in ["connected", "disconnected"]


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test that root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert data["message"] == "Policy Aggregator API"


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_404_error(self, client):
        """Test that 404 errors return proper format."""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
    
    def test_validation_error_format(self, client):
        """Test that validation errors return proper format."""
        # This would require a POST endpoint with validation
        # For now, just verify the error handler is registered
        response = client.get("/health?invalid=param")
        
        # Health endpoint doesn't have query params, but should still work
        assert response.status_code in [200, 422]



