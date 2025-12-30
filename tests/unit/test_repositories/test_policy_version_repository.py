"""Unit tests for PolicyVersionRepository."""

import pytest
import uuid
from datetime import datetime
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.repositories.source_repository import SourceRepository
from api.models.db.policy_version import PolicyVersion
from api.utils.hashing import generate_hash


@pytest.mark.asyncio
class TestPolicyVersionRepository:
    """Tests for PolicyVersionRepository."""
    
    async def test_create_policy_version(self, db_session, sample_source_data):
        """Test creating a policy version."""
        # Create source first
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create policy version
        repo = PolicyVersionRepository(db_session)
        version_data = {
            "source_id": source.id,
            "content_hash": generate_hash("test content"),
            "raw_text": "test content",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 12,
            "fetch_duration": 100
        }
        version = await repo.create(version_data)
        
        assert version.id is not None
        assert version.source_id == source.id
        assert len(version.content_hash) == 64
    
    async def test_get_by_id(self, db_session, sample_source_data):
        """Test getting policy version by ID."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        repo = PolicyVersionRepository(db_session)
        version_data = {
            "source_id": source.id,
            "content_hash": generate_hash("test"),
            "raw_text": "test",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 4,
            "fetch_duration": 50
        }
        created = await repo.create(version_data)
        
        retrieved = await repo.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    async def test_get_by_source_id(self, db_session, sample_source_data):
        """Test getting policy versions by source ID."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        repo = PolicyVersionRepository(db_session)
        
        # Create multiple versions
        version1_data = {
            "source_id": source.id,
            "content_hash": generate_hash("content 1"),
            "raw_text": "content 1",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 9,
            "fetch_duration": 100
        }
        version1 = await repo.create(version1_data)
        
        version2_data = {
            "source_id": source.id,
            "content_hash": generate_hash("content 2"),
            "raw_text": "content 2",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 9,
            "fetch_duration": 100
        }
        version2 = await repo.create(version2_data)
        
        versions = await repo.get_by_source_id(source.id)
        
        assert len(versions) == 2
        assert any(v.id == version1.id for v in versions)
        assert any(v.id == version2.id for v in versions)
    
    async def test_get_latest_by_source_id(self, db_session, sample_source_data):
        """Test getting latest policy version by source ID."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        repo = PolicyVersionRepository(db_session)
        
        # Create two versions with different timestamps
        from datetime import timedelta
        now = datetime.utcnow()
        
        version1_data = {
            "source_id": source.id,
            "content_hash": generate_hash("old"),
            "raw_text": "old",
            "fetched_at": now - timedelta(hours=1),
            "normalized_at": now - timedelta(hours=1),
            "content_length": 3,
            "fetch_duration": 50
        }
        await repo.create(version1_data)
        
        version2_data = {
            "source_id": source.id,
            "content_hash": generate_hash("new"),
            "raw_text": "new",
            "fetched_at": now,
            "normalized_at": now,
            "content_length": 3,
            "fetch_duration": 50
        }
        version2 = await repo.create(version2_data)
        
        latest = await repo.get_latest_by_source_id(source.id)
        
        assert latest is not None
        assert latest.id == version2.id
    
    async def test_get_by_hash(self, db_session, sample_source_data):
        """Test getting policy version by hash."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        repo = PolicyVersionRepository(db_session)
        content_hash = generate_hash("test content")
        version_data = {
            "source_id": source.id,
            "content_hash": content_hash,
            "raw_text": "test content",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 12,
            "fetch_duration": 100
        }
        created = await repo.create(version_data)
        
        retrieved = await repo.get_by_hash(content_hash)
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    async def test_exists_by_hash(self, db_session, sample_source_data):
        """Test checking if version exists by hash."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        repo = PolicyVersionRepository(db_session)
        content_hash = generate_hash("test")
        version_data = {
            "source_id": source.id,
            "content_hash": content_hash,
            "raw_text": "test",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 4,
            "fetch_duration": 50
        }
        await repo.create(version_data)
        
        exists = await repo.exists_by_hash(source.id, content_hash)
        assert exists is True
        
        not_exists = await repo.exists_by_hash(source.id, "a" * 64)
        assert not_exists is False




