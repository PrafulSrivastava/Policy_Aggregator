"""Integration tests for trigger web routes."""

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


class TestTriggerPage:
    """Tests for GET /trigger web route."""
    
    @pytest.mark.asyncio
    async def test_trigger_page_with_authentication(
        self, client, test_user, sample_source
    ):
        """Test accessing trigger page with valid authentication."""
        # Login first to get session cookie
        login_response = client.post(
            "/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        
        assert login_response.status_code == 200 or login_response.status_code == 302
        
        # Access trigger page
        response = client.get("/trigger")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Manual Trigger" in response.text
        assert "Fetch Now" in response.text
        assert sample_source.name in response.text or "Germany" in response.text
    
    def test_trigger_page_without_authentication(self, client):
        """Test accessing trigger page without authentication redirects to login."""
        response = client.get("/trigger", follow_redirects=False)
        
        # Should redirect to login
        assert response.status_code == 302 or response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_trigger_page_displays_sources(
        self, client, test_user, db_session
    ):
        """Test trigger page displays all sources."""
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
        
        # Access trigger page
        response = client.get("/trigger")
        
        assert response.status_code == 200
        # Check both sources are displayed
        assert "Source 1" in response.text or "DE" in response.text
        assert "Source 2" in response.text or "FR" in response.text
    
    @pytest.mark.asyncio
    async def test_trigger_page_shows_source_details(
        self, client, test_user, sample_source
    ):
        """Test trigger page shows source details correctly."""
        # Login
        login_response = client.post(
            "/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        
        # Access trigger page
        response = client.get("/trigger")
        
        assert response.status_code == 200
        # Check source details are displayed
        assert sample_source.country in response.text
        assert sample_source.visa_type in response.text
        assert sample_source.fetch_type.upper() in response.text

