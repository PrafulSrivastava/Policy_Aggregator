"""Unit tests for SourceRepository."""

import pytest
import uuid
from datetime import datetime
from api.repositories.source_repository import SourceRepository
from api.models.db.source import Source


@pytest.mark.asyncio
class TestSourceRepository:
    """Tests for SourceRepository."""
    
    async def test_create_source(self, db_session, sample_source_data):
        """Test creating a source."""
        repo = SourceRepository(db_session)
        source = await repo.create(sample_source_data)
        
        assert source.id is not None
        assert source.country == "DE"
        assert source.visa_type == "Student"
        assert source.is_active is True
    
    async def test_get_by_id(self, db_session, sample_source_data):
        """Test getting source by ID."""
        repo = SourceRepository(db_session)
        created = await repo.create(sample_source_data)
        
        retrieved = await repo.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.country == "DE"
    
    async def test_get_by_id_not_found(self, db_session):
        """Test getting non-existent source."""
        repo = SourceRepository(db_session)
        result = await repo.get_by_id(uuid.uuid4())
        
        assert result is None
    
    async def test_list_all(self, db_session, sample_source_data):
        """Test listing all sources."""
        repo = SourceRepository(db_session)
        
        # Create multiple sources
        source1 = await repo.create(sample_source_data)
        source2_data = sample_source_data.copy()
        source2_data["name"] = "Another Source"
        source2 = await repo.create(source2_data)
        
        all_sources = await repo.list_all()
        
        assert len(all_sources) >= 2
        assert any(s.id == source1.id for s in all_sources)
        assert any(s.id == source2.id for s in all_sources)
    
    async def test_list_active(self, db_session, sample_source_data):
        """Test listing active sources."""
        repo = SourceRepository(db_session)
        
        # Create active and inactive sources
        active_source = await repo.create(sample_source_data)
        inactive_data = sample_source_data.copy()
        inactive_data["is_active"] = False
        inactive_source = await repo.create(inactive_data)
        
        active_sources = await repo.list_active()
        
        assert any(s.id == active_source.id for s in active_sources)
        assert not any(s.id == inactive_source.id for s in active_sources)
    
    async def test_update_source(self, db_session, sample_source_data):
        """Test updating a source."""
        repo = SourceRepository(db_session)
        source = await repo.create(sample_source_data)
        
        updated = await repo.update(source.id, {"name": "Updated Name"})
        
        assert updated.name == "Updated Name"
        assert updated.id == source.id
    
    async def test_update_source_not_found(self, db_session):
        """Test updating non-existent source."""
        repo = SourceRepository(db_session)
        
        with pytest.raises(ValueError, match="not found"):
            await repo.update(uuid.uuid4(), {"name": "Updated"})
    
    async def test_delete_source(self, db_session, sample_source_data):
        """Test deleting a source."""
        repo = SourceRepository(db_session)
        source = await repo.create(sample_source_data)
        
        result = await repo.delete(source.id)
        
        assert result is True
        deleted = await repo.get_by_id(source.id)
        assert deleted is None
    
    async def test_delete_source_not_found(self, db_session):
        """Test deleting non-existent source."""
        repo = SourceRepository(db_session)
        result = await repo.delete(uuid.uuid4())
        
        assert result is False
    
    async def test_get_by_country_visa(self, db_session, sample_source_data):
        """Test getting sources by country and visa type."""
        repo = SourceRepository(db_session)
        
        # Create sources with different countries
        source1 = await repo.create(sample_source_data)
        source2_data = sample_source_data.copy()
        source2_data["country"] = "FR"
        source2 = await repo.create(source2_data)
        
        de_sources = await repo.get_by_country_visa("DE", "Student")
        
        assert any(s.id == source1.id for s in de_sources)
        assert not any(s.id == source2.id for s in de_sources)





