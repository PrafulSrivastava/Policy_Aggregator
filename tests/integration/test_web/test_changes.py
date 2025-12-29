"""Integration tests for change web routes."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timedelta

from api.main import app
from api.database import get_db
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.user_repository import UserRepository
from api.auth.auth import get_password_hash, create_access_token
from tests.fixtures.alert_fixtures import create_test_policy_change, create_test_policy_version


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
    from api.repositories.source_repository import SourceRepository
    source_repo = SourceRepository(db_session)
    source_data = {
        "country": "DE",
        "visa_type": "Student",
        "url": "https://example.com/student-visa",
        "name": "Germany Student Visa Source",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "metadata": {}
    }
    source = await source_repo.create(source_data)
    await db_session.commit()
    return source


@pytest.fixture
async def sample_policy_change(db_session, sample_source):
    """Create a sample policy change with versions."""
    # Create old version
    old_version = await create_test_policy_version(
        db_session,
        sample_source.id,
        content_hash="a" * 64,
        raw_text="Old policy content"
    )
    
    # Create new version
    new_version = await create_test_policy_version(
        db_session,
        sample_source.id,
        content_hash="b" * 64,
        raw_text="New policy content"
    )
    
    # Create policy change
    change = await create_test_policy_change(
        db_session,
        sample_source.id,
        old_hash="a" * 64,
        new_hash="b" * 64,
        diff="--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Old policy content\n+New policy content",
        old_version_id=old_version.id,
        new_version_id=new_version.id
    )
    await db_session.commit()
    return change


class TestChangeDetailPage:
    """Tests for GET /changes/{id} web route."""
    
    @pytest.mark.asyncio
    async def test_change_detail_page_with_authentication(
        self, client, test_user, sample_policy_change
    ):
        """Test accessing change detail page with valid authentication."""
        # Login first to get session cookie
        login_response = client.post(
            "/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        
        assert login_response.status_code == 200 or login_response.status_code == 302
        
        # Access change detail page
        response = client.get(f"/changes/{sample_policy_change.id}")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Change Detail" in response.text
        assert "Diff" in response.text
        assert sample_policy_change.diff[:50] in response.text  # Check diff is in page
    
    def test_change_detail_page_without_authentication(self, client, sample_policy_change):
        """Test accessing change detail page without authentication redirects to login."""
        response = client.get(f"/changes/{sample_policy_change.id}", follow_redirects=False)
        
        # Should redirect to login
        assert response.status_code == 302 or response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_change_detail_page_not_found(
        self, client, test_user
    ):
        """Test accessing change detail page for non-existent change returns 404."""
        # Login first
        login_response = client.post(
            "/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        
        # Access non-existent change
        fake_id = uuid4()
        response = client.get(f"/changes/{fake_id}")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_change_detail_page_navigation_buttons(
        self, client, test_user, db_session, sample_source
    ):
        """Test change detail page shows navigation buttons correctly."""
        # Create multiple changes with different timestamps
        change1 = await create_test_policy_change(
            db_session,
            sample_source.id
        )
        change1.detected_at = datetime.utcnow() - timedelta(hours=2)
        db_session.add(change1)
        
        change2 = await create_test_policy_change(
            db_session,
            sample_source.id
        )
        change2.detected_at = datetime.utcnow() - timedelta(hours=1)
        db_session.add(change2)
        
        change3 = await create_test_policy_change(
            db_session,
            sample_source.id
        )
        change3.detected_at = datetime.utcnow()
        db_session.add(change3)
        
        await db_session.commit()
        
        # Login
        login_response = client.post(
            "/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        
        # Access middle change
        response = client.get(f"/changes/{change2.id}")
        
        assert response.status_code == 200
        # Should have previous and next buttons
        assert "Previous" in response.text
        assert "Next" in response.text
        assert str(change1.id) in response.text  # Previous change ID
        assert str(change3.id) in response.text  # Next change ID

