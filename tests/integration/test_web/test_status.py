"""Integration tests for status web routes."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.database import get_db
from api.repositories.source_repository import SourceRepository
from api.repositories.user_repository import UserRepository
from api.auth.auth import get_password_hash
from tests.fixtures.alert_fixtures import create_test_source


@pytest.fixture
async def client(db_session):
    """Create a test client for the FastAPI app with database dependency override."""
    # Override get_db dependency to use test database session
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app, follow_redirects=False)
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


class TestStatusPage:
    """Tests for GET /status web route."""
    
    @pytest.mark.asyncio
    async def test_status_page_with_authentication(
        self, client, test_user, sample_source
    ):
        """Test accessing status page with valid authentication."""
        # Login first to get session cookie
        login_response = client.post(
            "/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        
        assert login_response.status_code == 200 or login_response.status_code == 302
        
        # Access status page
        response = client.get("/status")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "System Status" in response.text
        assert "Total Sources" in response.text
        assert "Healthy" in response.text
        assert sample_source.name in response.text or "Germany" in response.text
    
    def test_status_page_without_authentication(self, client):
        """Test accessing status page without authentication redirects to login."""
        response = client.get("/status", follow_redirects=False)
        
        # Should redirect to login
        assert response.status_code == 302 or response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_status_page_displays_statistics(
        self, client, test_user, db_session
    ):
        """Test status page displays system statistics."""
        # Create multiple sources
        source1 = await create_test_source(
            db_session,
            country="DE",
            visa_type="Student",
            name="Source 1"
        )
        source2 = await create_test_source(
            db_session,
            country="FR",
            visa_type="Work",
            name="Source 2"
        )
        await db_session.commit()
        
        # Login
        login_response = client.post(
            "/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        
        # Access status page
        response = client.get("/status")
        
        assert response.status_code == 200
        # Check statistics cards are displayed
        assert "Total Sources" in response.text
        assert "Healthy" in response.text
        assert "Errors" in response.text
        assert "Stale" in response.text
    
    @pytest.mark.asyncio
    async def test_status_page_shows_source_status(
        self, client, test_user, sample_source
    ):
        """Test status page shows source status indicators."""
        # Login
        login_response = client.post(
            "/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        
        # Access status page
        response = client.get("/status")
        
        assert response.status_code == 200
        # Check status indicators are present
        assert "Healthy" in response.text or "Error" in response.text or "Stale" in response.text or "Never Checked" in response.text
        # Check table headers
        assert "Last Checked" in response.text
        assert "Last Change" in response.text
        assert "Next Check" in response.text

