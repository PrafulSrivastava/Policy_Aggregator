"""Integration tests for status API endpoint."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

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
async def sample_sources(db_session):
    """Create sample sources with different statuses."""
    sources = []
    
    # Healthy source (checked recently)
    source1 = await create_test_source(
        db_session,
        country="DE",
        visa_type="Student",
        name="Healthy Source"
    )
    source1.last_checked_at = datetime.utcnow() - timedelta(hours=12)
    source1.consecutive_fetch_failures = 0
    db_session.add(source1)
    sources.append(source1)
    
    # Error source (has failures)
    source2 = await create_test_source(
        db_session,
        country="FR",
        visa_type="Work",
        name="Error Source"
    )
    source2.consecutive_fetch_failures = 3
    source2.last_fetch_error = "Connection timeout"
    db_session.add(source2)
    sources.append(source2)
    
    # Stale source (not checked recently)
    source3 = await create_test_source(
        db_session,
        country="UK",
        visa_type="Student",
        name="Stale Source"
    )
    source3.last_checked_at = datetime.utcnow() - timedelta(days=3)
    source3.check_frequency = "daily"
    source3.consecutive_fetch_failures = 0
    db_session.add(source3)
    sources.append(source3)
    
    # Never checked source
    source4 = await create_test_source(
        db_session,
        country="CA",
        visa_type="Work",
        name="Never Checked Source"
    )
    source4.last_checked_at = None
    source4.consecutive_fetch_failures = 0
    db_session.add(source4)
    sources.append(source4)
    
    await db_session.commit()
    return sources


class TestGetSystemStatus:
    """Tests for GET /api/status endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_status_with_authentication(
        self, client, test_user, sample_sources
    ):
        """Test getting system status with valid authentication."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            "/api/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "sources" in data
        assert "statistics" in data
        assert "last_daily_job_run" in data
        
        # Check statistics structure
        stats = data["statistics"]
        assert "total_sources" in stats
        assert "healthy_sources" in stats
        assert "error_sources" in stats
        assert "stale_sources" in stats
        assert "never_checked_sources" in stats
        
        # Check sources list
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) >= len(sample_sources)
    
    def test_get_status_without_authentication(self, client):
        """Test getting system status without authentication returns 401."""
        response = client.get("/api/status")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_status_sources_sorted_by_priority(
        self, client, test_user, sample_sources
    ):
        """Test sources are sorted by status priority (errors first)."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            "/api/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        sources = data["sources"]
        assert len(sources) >= 4
        
        # Find our test sources
        error_source = next((s for s in sources if s["name"] == "Error Source"), None)
        stale_source = next((s for s in sources if s["name"] == "Stale Source"), None)
        never_checked_source = next((s for s in sources if s["name"] == "Never Checked Source"), None)
        healthy_source = next((s for s in sources if s["name"] == "Healthy Source"), None)
        
        # Verify all sources found
        assert error_source is not None
        assert stale_source is not None
        assert never_checked_source is not None
        assert healthy_source is not None
        
        # Verify status values
        assert error_source["status"] == "error"
        assert stale_source["status"] == "stale"
        assert never_checked_source["status"] == "never_checked"
        assert healthy_source["status"] == "healthy"
        
        # Verify sorting: error should come before stale, stale before never_checked, never_checked before healthy
        error_idx = sources.index(error_source)
        stale_idx = sources.index(stale_source)
        never_checked_idx = sources.index(never_checked_source)
        healthy_idx = sources.index(healthy_source)
        
        assert error_idx < stale_idx
        assert stale_idx < never_checked_idx
        assert never_checked_idx < healthy_idx
    
    @pytest.mark.asyncio
    async def test_status_includes_next_check_time(
        self, client, test_user, sample_sources
    ):
        """Test status includes next check time for sources."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            "/api/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find healthy source (should have next_check_time)
        healthy_source = next((s for s in data["sources"] if s["name"] == "Healthy Source"), None)
        assert healthy_source is not None
        assert "next_check_time" in healthy_source
        # Should have next check time if last_checked_at exists and frequency is daily/weekly
        if healthy_source["last_checked_at"] and healthy_source["check_frequency"] in ["daily", "weekly"]:
            assert healthy_source["next_check_time"] is not None
    
    @pytest.mark.asyncio
    async def test_status_statistics_accurate(
        self, client, test_user, sample_sources
    ):
        """Test status statistics are calculated correctly."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            "/api/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        stats = data["statistics"]
        
        # Verify counts match expected values (at least our test sources)
        assert stats["total_sources"] >= 4
        assert stats["healthy_sources"] >= 1
        assert stats["error_sources"] >= 1
        assert stats["stale_sources"] >= 1
        assert stats["never_checked_sources"] >= 1
        
        # Verify sum matches total
        total_calculated = (
            stats["healthy_sources"] +
            stats["error_sources"] +
            stats["stale_sources"] +
            stats["never_checked_sources"]
        )
        assert total_calculated == stats["total_sources"]

