"""Integration tests for change API endpoints."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timedelta

from api.main import app
from api.database import get_db
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.repositories.source_repository import SourceRepository
from api.repositories.route_subscription_repository import RouteSubscriptionRepository
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
async def sample_route(db_session, sample_source):
    """Create a sample route subscription."""
    route_repo = RouteSubscriptionRepository(db_session)
    route_data = {
        "origin_country": "IN",
        "destination_country": "DE",
        "visa_type": "Student",
        "email": "test@example.com",
        "is_active": True
    }
    route = await route_repo.create(route_data)
    await db_session.commit()
    return route


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


class TestGetChangeDetail:
    """Tests for GET /api/changes/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_change_detail_with_authentication(
        self, client, test_user, sample_policy_change
    ):
        """Test getting change detail with valid authentication."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            f"/api/changes/{sample_policy_change.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "id" in data
        assert "detected_at" in data
        assert "diff" in data
        assert "diff_length" in data
        assert "source" in data
        assert "old_version" in data
        assert "new_version" in data
        
        # Check source information
        assert data["source"]["id"] == str(sample_policy_change.source_id)
        assert data["source"]["name"] == "Germany Student Visa Source"
        
        # Check versions
        assert data["old_version"] is not None
        assert data["new_version"] is not None
        assert data["old_version"]["raw_text"] == "Old policy content"
        assert data["new_version"]["raw_text"] == "New policy content"
    
    def test_get_change_detail_without_authentication(self, client, sample_policy_change):
        """Test getting change detail without authentication returns 401."""
        response = client.get(f"/api/changes/{sample_policy_change.id}")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_change_detail_not_found(self, client, test_user):
        """Test getting change detail for non-existent change returns 404."""
        auth_token = create_access_token(data={"sub": test_user.username})
        fake_id = uuid4()
        response = client.get(
            f"/api/changes/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "CHANGE_NOT_FOUND" in data["detail"]["code"]
    
    @pytest.mark.asyncio
    async def test_get_change_detail_with_navigation(
        self, client, test_user, db_session, sample_source
    ):
        """Test getting change detail includes previous/next navigation."""
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
        
        auth_token = create_access_token(data={"sub": test_user.username})
        
        # Get middle change - should have previous and next
        response = client.get(
            f"/api/changes/{change2.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have navigation
        assert "previous_change_id" in data
        assert "next_change_id" in data
        assert data["previous_change_id"] == str(change1.id)
        assert data["next_change_id"] == str(change3.id)


class TestDownloadChangeDiff:
    """Tests for GET /api/changes/{id}/download endpoint."""
    
    @pytest.mark.asyncio
    async def test_download_change_diff_with_authentication(
        self, client, test_user, sample_policy_change
    ):
        """Test downloading change diff with valid authentication."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            f"/api/changes/{sample_policy_change.id}/download",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert sample_policy_change.diff in response.text
    
    def test_download_change_diff_without_authentication(self, client, sample_policy_change):
        """Test downloading change diff without authentication returns 401."""
        response = client.get(f"/api/changes/{sample_policy_change.id}/download")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_download_change_diff_not_found(self, client, test_user):
        """Test downloading change diff for non-existent change returns 404."""
        auth_token = create_access_token(data={"sub": test_user.username})
        fake_id = uuid4()
        response = client.get(
            f"/api/changes/{fake_id}/download",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404

