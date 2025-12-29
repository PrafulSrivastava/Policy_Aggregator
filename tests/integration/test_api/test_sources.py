"""Integration tests for source API endpoints."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from api.main import app
from api.database import get_db
from api.repositories.source_repository import SourceRepository
from api.repositories.user_repository import UserRepository
from api.auth.auth import get_password_hash, create_access_token


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


class TestListSources:
    """Tests for GET /api/sources endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_sources_with_authentication(self, client, test_user, sample_source):
        """Test listing sources with valid authentication."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            "/api/sources",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 1
        assert data["page"] == 1
        assert data["page_size"] == 20
    
    def test_list_sources_without_authentication(self, client):
        """Test listing sources without authentication returns 401."""
        response = client.get("/api/sources")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_sources_pagination(self, client, test_user, db_session):
        """Test pagination parameters."""
        auth_token = create_access_token(data={"sub": test_user.username})
        # Create multiple sources
        source_repo = SourceRepository(db_session)
        for i in range(5):
            source_data = {
                "country": "DE",
                "visa_type": f"Student{i}",
                "url": f"https://example.com/student{i}",
                "name": f"Source {i}",
                "fetch_type": "html",
                "check_frequency": "daily",
                "is_active": True,
                "metadata": {}
            }
            await source_repo.create(source_data)
        await db_session.commit()
        
        # Test first page
        response = client.get(
            "/api/sources?page=1&page_size=2",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2
    
    @pytest.mark.asyncio
    async def test_list_sources_filter_by_country(self, client, test_user, db_session):
        """Test filtering by country."""
        auth_token = create_access_token(data={"sub": test_user.username})
        source_repo = SourceRepository(db_session)
        
        # Create sources with different countries
        source1_data = {
            "country": "DE",
            "visa_type": "Student",
            "url": "https://example.com/de",
            "name": "Germany Source",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "metadata": {}
        }
        source2_data = {
            "country": "FR",
            "visa_type": "Student",
            "url": "https://example.com/fr",
            "name": "France Source",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "metadata": {}
        }
        await source_repo.create(source1_data)
        await source_repo.create(source2_data)
        await db_session.commit()
        
        # Filter by country
        response = client.get(
            "/api/sources?country=DE",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["country"] == "DE" for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_list_sources_filter_by_visa_type(self, client, test_user, db_session):
        """Test filtering by visa type."""
        auth_token = create_access_token(data={"sub": test_user.username})
        source_repo = SourceRepository(db_session)
        
        # Create sources with different visa types
        source1_data = {
            "country": "DE",
            "visa_type": "Student",
            "url": "https://example.com/student",
            "name": "Student Source",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "metadata": {}
        }
        source2_data = {
            "country": "DE",
            "visa_type": "Work",
            "url": "https://example.com/work",
            "name": "Work Source",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "metadata": {}
        }
        await source_repo.create(source1_data)
        await source_repo.create(source2_data)
        await db_session.commit()
        
        # Filter by visa type
        response = client.get(
            "/api/sources?visa_type=Student",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["visa_type"] == "Student" for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_list_sources_filter_by_is_active(self, client, test_user, db_session):
        """Test filtering by is_active."""
        auth_token = create_access_token(data={"sub": test_user.username})
        source_repo = SourceRepository(db_session)
        
        # Create active and inactive sources
        active_source_data = {
            "country": "DE",
            "visa_type": "Student",
            "url": "https://example.com/active",
            "name": "Active Source",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "metadata": {}
        }
        inactive_source_data = {
            "country": "DE",
            "visa_type": "Student",
            "url": "https://example.com/inactive",
            "name": "Inactive Source",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": False,
            "metadata": {}
        }
        await source_repo.create(active_source_data)
        await source_repo.create(inactive_source_data)
        await db_session.commit()
        
        # Filter by is_active
        response = client.get(
            "/api/sources?is_active=true",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["is_active"] is True for item in data["items"])


class TestCreateSource:
    """Tests for POST /api/sources endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_source_with_valid_data(self, client, test_user):
        """Test creating a source with valid data."""
        auth_token = create_access_token(data={"sub": test_user.username})
        source_data = {
            "country": "DE",
            "visa_type": "Work",
            "url": "https://example.com/work-visa",
            "name": "Germany Work Visa Source",
            "fetch_type": "html",
            "check_frequency": "weekly",
            "is_active": True,
            "metadata": {}
        }
        
        response = client.post(
            "/api/sources",
            json=source_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["country"] == "DE"
        assert data["visa_type"] == "Work"
        assert data["url"] == "https://example.com/work-visa"
        assert data["name"] == "Germany Work Visa Source"
        assert data["fetch_type"] == "html"
        assert data["check_frequency"] == "weekly"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_source_without_authentication(self, client):
        """Test creating a source without authentication returns 401."""
        source_data = {
            "country": "DE",
            "visa_type": "Student",
            "url": "https://example.com/policy",
            "name": "Test Source",
            "fetch_type": "html",
            "check_frequency": "daily"
        }
        
        response = client.post("/api/sources", json=source_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_source_with_invalid_data(self, client, test_user):
        """Test creating a source with invalid data returns 422."""
        auth_token = create_access_token(data={"sub": test_user.username})
        # Missing required field
        source_data = {
            "country": "DE",
            "visa_type": "Student"
            # Missing url, name, fetch_type, check_frequency
        }
        
        response = client.post(
            "/api/sources",
            json=source_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_source_with_invalid_url(self, client, test_user):
        """Test creating a source with invalid URL returns 422."""
        auth_token = create_access_token(data={"sub": test_user.username})
        source_data = {
            "country": "DE",
            "visa_type": "Student",
            "url": "invalid-url",  # Invalid URL format
            "name": "Test Source",
            "fetch_type": "html",
            "check_frequency": "daily"
        }
        
        response = client.post(
            "/api/sources",
            json=source_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_source_duplicate(self, client, test_user, sample_source):
        """Test creating a duplicate source returns 409."""
        auth_token = create_access_token(data={"sub": test_user.username})
        source_data = {
            "country": "DE",
            "visa_type": "Student",
            "url": "https://example.com/student-visa",  # Same as sample_source
            "name": "Duplicate Source",
            "fetch_type": "html",
            "check_frequency": "daily"
        }
        
        response = client.post(
            "/api/sources",
            json=source_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "DUPLICATE_SOURCE" in str(data["detail"])


class TestGetSource:
    """Tests for GET /api/sources/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_source_with_valid_id(self, client, test_user, sample_source):
        """Test getting a source with valid ID."""
        auth_token = create_access_token(data={"sub": test_user.username})
        response = client.get(
            f"/api/sources/{sample_source.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(sample_source.id)
        assert data["country"] == "DE"
        assert data["visa_type"] == "Student"
        assert "last_checked_at" in data
        assert "last_change_detected_at" in data
    
    def test_get_source_without_authentication(self, client, sample_source):
        """Test getting a source without authentication returns 401."""
        response = client.get(f"/api/sources/{sample_source.id}")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_source_with_invalid_id(self, client, test_user):
        """Test getting a source with invalid ID returns 404."""
        auth_token = create_access_token(data={"sub": test_user.username})
        invalid_id = uuid4()
        
        response = client.get(
            f"/api/sources/{invalid_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "SOURCE_NOT_FOUND" in str(data["detail"])


class TestUpdateSource:
    """Tests for PUT /api/sources/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_source_with_valid_data(self, client, test_user, sample_source):
        """Test updating a source with valid data."""
        auth_token = create_access_token(data={"sub": test_user.username})
        update_data = {
            "name": "Updated Source Name",
            "is_active": False
        }
        
        response = client.put(
            f"/api/sources/{sample_source.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated Source Name"
        assert data["is_active"] is False
        assert data["id"] == str(sample_source.id)
    
    @pytest.mark.asyncio
    async def test_update_source_partial(self, client, test_user, sample_source):
        """Test partial update of a source."""
        auth_token = create_access_token(data={"sub": test_user.username})
        update_data = {
            "check_frequency": "weekly"
        }
        
        response = client.put(
            f"/api/sources/{sample_source.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["check_frequency"] == "weekly"
        # Other fields should remain unchanged
        assert data["country"] == "DE"
        assert data["visa_type"] == "Student"
    
    def test_update_source_without_authentication(self, client, sample_source):
        """Test updating a source without authentication returns 401."""
        update_data = {"name": "Updated Name"}
        
        response = client.put(f"/api/sources/{sample_source.id}", json=update_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_update_source_with_invalid_id(self, client, test_user):
        """Test updating a source with invalid ID returns 404."""
        auth_token = create_access_token(data={"sub": test_user.username})
        invalid_id = uuid4()
        update_data = {"name": "Updated Name"}
        
        response = client.put(
            f"/api/sources/{invalid_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "SOURCE_NOT_FOUND" in str(data["detail"])


class TestDeleteSource:
    """Tests for DELETE /api/sources/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_source_with_valid_id(self, client, test_user, db_session):
        """Test deleting a source with valid ID."""
        auth_token = create_access_token(data={"sub": test_user.username})
        # Create a source to delete
        source_repo = SourceRepository(db_session)
        source_data = {
            "country": "FR",
            "visa_type": "Work",
            "url": "https://example.com/delete",
            "name": "Source to Delete",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "metadata": {}
        }
        source = await source_repo.create(source_data)
        await db_session.commit()
        
        response = client.delete(
            f"/api/sources/{source.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 204
        
        # Verify source is deleted
        deleted_source = await source_repo.get_by_id(source.id)
        assert deleted_source is None
    
    def test_delete_source_without_authentication(self, client, sample_source):
        """Test deleting a source without authentication returns 401."""
        response = client.delete(f"/api/sources/{sample_source.id}")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_delete_source_with_invalid_id(self, client, test_user):
        """Test deleting a source with invalid ID returns 404."""
        auth_token = create_access_token(data={"sub": test_user.username})
        invalid_id = uuid4()
        
        response = client.delete(
            f"/api/sources/{invalid_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "SOURCE_NOT_FOUND" in str(data["detail"])

