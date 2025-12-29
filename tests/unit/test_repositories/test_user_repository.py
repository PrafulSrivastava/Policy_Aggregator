"""Unit tests for UserRepository."""

import pytest
import uuid
from api.repositories.user_repository import UserRepository
from api.models.db.user import User


@pytest.mark.asyncio
class TestUserRepository:
    """Tests for UserRepository."""
    
    async def test_create_user(self, db_session, sample_user_data):
        """Test creating a user."""
        repo = UserRepository(db_session)
        user = await repo.create(sample_user_data)
        
        assert user.id is not None
        assert user.username == "admin"
        assert user.hashed_password == sample_user_data["hashed_password"]
        assert user.is_active is True
    
    async def test_get_by_id(self, db_session, sample_user_data):
        """Test getting user by ID."""
        repo = UserRepository(db_session)
        created = await repo.create(sample_user_data)
        
        retrieved = await repo.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.username == "admin"
    
    async def test_get_by_id_not_found(self, db_session):
        """Test getting non-existent user."""
        repo = UserRepository(db_session)
        result = await repo.get_by_id(uuid.uuid4())
        
        assert result is None
    
    async def test_get_by_username(self, db_session, sample_user_data):
        """Test getting user by username."""
        repo = UserRepository(db_session)
        created = await repo.create(sample_user_data)
        
        retrieved = await repo.get_by_username("admin")
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.username == "admin"
    
    async def test_get_by_username_not_found(self, db_session):
        """Test getting non-existent user by username."""
        repo = UserRepository(db_session)
        result = await repo.get_by_username("nonexistent")
        
        assert result is None
    
    async def test_update_user(self, db_session, sample_user_data):
        """Test updating a user."""
        repo = UserRepository(db_session)
        user = await repo.create(sample_user_data)
        
        updated = await repo.update(user.id, {"is_active": False})
        
        assert updated.is_active is False
        assert updated.id == user.id
        assert updated.username == "admin"
    
    async def test_update_user_not_found(self, db_session):
        """Test updating non-existent user."""
        repo = UserRepository(db_session)
        
        with pytest.raises(ValueError, match="not found"):
            await repo.update(uuid.uuid4(), {"is_active": False})


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "admin",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5",  # Mock bcrypt hash
        "is_active": True
    }

