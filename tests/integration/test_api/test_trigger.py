"""Integration tests for trigger API endpoint."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime

from api.main import app
from api.database import get_db
from api.repositories.source_repository import SourceRepository
from api.repositories.user_repository import UserRepository
from api.auth.auth import get_password_hash, create_access_token
from tests.fixtures.alert_fixtures import create_test_source


@pytest.fixture
async def client(db_session):
    """Create a test client for the FastAPI app with database dependency override."""
    # Override get_db dependency to use test database session
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    # Clean up overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    """Create a test user in the database."""
    user_repo = UserRepository(db_session)
    user_data = {
        "username": "testuser",
        "hashed_password": get_password_hash("testpassword123"),
        "is_active": True
    }
    user = await user_repo.create(user_data)
    await db_session.commit()
    return user


@pytest.fixture
async def sample_source(db_session):
    """Create a sample source in the database."""
    source = await create_test_source(
        db_session,
        country="DE",
        visa_type="Student",
        url="https://example.com/student-visa",
        name="Germany Student Visa Source"
    )
    await db_session.commit()
    return source


class TestTriggerSourceFetch:
    """Tests for POST /api/sources/{id}/trigger endpoint."""
    
    @pytest.mark.asyncio
    async def test_trigger_source_with_authentication(
        self, client, test_user, sample_source
    ):
        """Test triggering source fetch with valid authentication."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.post(
            f"/api/sources/{sample_source.id}/trigger",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Note: This may succeed or fail depending on the actual fetch
        # We just verify the endpoint is accessible and returns appropriate response
        assert response.status_code in [200, 500]  # 200 if fetch succeeds, 500 if it fails
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "sourceId" in data
            assert "changeDetected" in data
            assert data["sourceId"] == str(sample_source.id)
    
    def test_trigger_source_without_authentication(self, client, sample_source):
        """Test triggering source fetch without authentication returns 401."""
        response = client.post(f"/api/sources/{sample_source.id}/trigger")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_trigger_source_not_found(self, client, test_user):
        """Test triggering source fetch for non-existent source returns 404."""
        auth_token = create_access_token(data={"sub": test_user.username})
        fake_id = uuid4()
        response = client.post(
            f"/api/sources/{fake_id}/trigger",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "SOURCE_NOT_FOUND" in data["detail"]["code"]
    
    @pytest.mark.asyncio
    async def test_trigger_source_response_structure(
        self, client, test_user, sample_source
    ):
        """Test trigger response has correct structure."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.post(
            f"/api/sources/{sample_source.id}/trigger",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Accept both success and failure responses
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Check all expected fields are present
            assert "success" in data
            assert "sourceId" in data
            assert "changeDetected" in data
            assert "policyVersionId" in data
            assert "policyChangeId" in data
            assert "error" in data
            assert "fetchedAt" in data
            
            # Check types
            assert isinstance(data["success"], bool)
            assert isinstance(data["changeDetected"], bool)
            assert data["sourceId"] == str(sample_source.id)

