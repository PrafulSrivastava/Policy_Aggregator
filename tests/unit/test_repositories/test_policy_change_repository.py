"""Unit tests for PolicyChangeRepository."""

import pytest
import uuid
from datetime import datetime, timedelta
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.repositories.source_repository import SourceRepository
from api.utils.hashing import generate_hash


@pytest.mark.asyncio
class TestPolicyChangeRepository:
    """Tests for PolicyChangeRepository."""
    
    async def test_create_policy_change(self, db_session, sample_source_data):
        """Test creating a policy change."""
        # Create source and versions
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        version_repo = PolicyVersionRepository(db_session)
        old_hash = generate_hash("old content")
        new_hash = generate_hash("new content")
        
        old_version_data = {
            "source_id": source.id,
            "content_hash": old_hash,
            "raw_text": "old content",
            "fetched_at": datetime.utcnow() - timedelta(hours=1),
            "normalized_at": datetime.utcnow() - timedelta(hours=1),
            "content_length": 11,
            "fetch_duration": 50
        }
        old_version = await version_repo.create(old_version_data)
        
        new_version_data = {
            "source_id": source.id,
            "content_hash": new_hash,
            "raw_text": "new content",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 11,
            "fetch_duration": 50
        }
        new_version = await version_repo.create(new_version_data)
        
        # Create policy change
        repo = PolicyChangeRepository(db_session)
        change_data = {
            "source_id": source.id,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "diff": "--- old content\n+++ new content",
            "detected_at": datetime.utcnow(),
            "old_version_id": old_version.id,
            "new_version_id": new_version.id,
            "diff_length": 30
        }
        change = await repo.create(change_data)
        
        assert change.id is not None
        assert change.source_id == source.id
        assert change.old_hash == old_hash
        assert change.new_hash == new_hash
    
    async def test_get_by_id(self, db_session, sample_source_data):
        """Test getting policy change by ID."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        version_repo = PolicyVersionRepository(db_session)
        old_hash = generate_hash("old")
        new_hash = generate_hash("new")
        
        old_version = await version_repo.create({
            "source_id": source.id,
            "content_hash": old_hash,
            "raw_text": "old",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 3,
            "fetch_duration": 50
        })
        
        new_version = await version_repo.create({
            "source_id": source.id,
            "content_hash": new_hash,
            "raw_text": "new",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 3,
            "fetch_duration": 50
        })
        
        repo = PolicyChangeRepository(db_session)
        change_data = {
            "source_id": source.id,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "diff": "diff",
            "detected_at": datetime.utcnow(),
            "old_version_id": old_version.id,
            "new_version_id": new_version.id,
            "diff_length": 4
        }
        created = await repo.create(change_data)
        
        retrieved = await repo.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    async def test_get_by_source_id(self, db_session, sample_source_data):
        """Test getting policy changes by source ID."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        version_repo = PolicyVersionRepository(db_session)
        repo = PolicyChangeRepository(db_session)
        
        # Create multiple changes
        old_hash1 = generate_hash("old1")
        new_hash1 = generate_hash("new1")
        old_v1 = await version_repo.create({
            "source_id": source.id,
            "content_hash": old_hash1,
            "raw_text": "old1",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 4,
            "fetch_duration": 50
        })
        new_v1 = await version_repo.create({
            "source_id": source.id,
            "content_hash": new_hash1,
            "raw_text": "new1",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 4,
            "fetch_duration": 50
        })
        change1 = await repo.create({
            "source_id": source.id,
            "old_hash": old_hash1,
            "new_hash": new_hash1,
            "diff": "diff1",
            "detected_at": datetime.utcnow(),
            "old_version_id": old_v1.id,
            "new_version_id": new_v1.id,
            "diff_length": 5
        })
        
        changes = await repo.get_by_source_id(source.id)
        
        assert len(changes) >= 1
        assert any(c.id == change1.id for c in changes)
    
    async def test_get_latest_by_source_id(self, db_session, sample_source_data):
        """Test getting latest policy change by source ID."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        version_repo = PolicyVersionRepository(db_session)
        repo = PolicyChangeRepository(db_session)
        
        now = datetime.utcnow()
        old_hash = generate_hash("old")
        new_hash1 = generate_hash("new1")
        new_hash2 = generate_hash("new2")
        
        old_v = await version_repo.create({
            "source_id": source.id,
            "content_hash": old_hash,
            "raw_text": "old",
            "fetched_at": now - timedelta(hours=2),
            "normalized_at": now - timedelta(hours=2),
            "content_length": 3,
            "fetch_duration": 50
        })
        
        new_v1 = await version_repo.create({
            "source_id": source.id,
            "content_hash": new_hash1,
            "raw_text": "new1",
            "fetched_at": now - timedelta(hours=1),
            "normalized_at": now - timedelta(hours=1),
            "content_length": 4,
            "fetch_duration": 50
        })
        
        new_v2 = await version_repo.create({
            "source_id": source.id,
            "content_hash": new_hash2,
            "raw_text": "new2",
            "fetched_at": now,
            "normalized_at": now,
            "content_length": 4,
            "fetch_duration": 50
        })
        
        # Create two changes
        await repo.create({
            "source_id": source.id,
            "old_hash": old_hash,
            "new_hash": new_hash1,
            "diff": "diff1",
            "detected_at": now - timedelta(hours=1),
            "old_version_id": old_v.id,
            "new_version_id": new_v1.id,
            "diff_length": 5
        })
        
        change2 = await repo.create({
            "source_id": source.id,
            "old_hash": new_hash1,
            "new_hash": new_hash2,
            "diff": "diff2",
            "detected_at": now,
            "old_version_id": new_v1.id,
            "new_version_id": new_v2.id,
            "diff_length": 5
        })
        
        latest = await repo.get_latest_by_source_id(source.id)
        
        assert latest is not None
        assert latest.id == change2.id
    
    async def test_get_by_route(self, db_session):
        """Test getting policy changes by route."""
        source_repo = SourceRepository(db_session)
        
        # Create source matching route
        source1_data = {
            "country": "DE",
            "visa_type": "Student",
            "url": "https://example.com/de-student",
            "name": "DE Student",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "metadata": {}
        }
        source1 = await source_repo.create(source1_data)
        
        # Create source not matching route
        source2_data = {
            "country": "FR",
            "visa_type": "Student",
            "url": "https://example.com/fr-student",
            "name": "FR Student",
            "fetch_type": "html",
            "check_frequency": "daily",
            "is_active": True,
            "metadata": {}
        }
        source2 = await source_repo.create(source2_data)
        
        version_repo = PolicyVersionRepository(db_session)
        repo = PolicyChangeRepository(db_session)
        
        # Create change for source1
        old_hash = generate_hash("old")
        new_hash = generate_hash("new")
        old_v = await version_repo.create({
            "source_id": source1.id,
            "content_hash": old_hash,
            "raw_text": "old",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 3,
            "fetch_duration": 50
        })
        new_v = await version_repo.create({
            "source_id": source1.id,
            "content_hash": new_hash,
            "raw_text": "new",
            "fetched_at": datetime.utcnow(),
            "normalized_at": datetime.utcnow(),
            "content_length": 3,
            "fetch_duration": 50
        })
        change1 = await repo.create({
            "source_id": source1.id,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "diff": "diff",
            "detected_at": datetime.utcnow(),
            "old_version_id": old_v.id,
            "new_version_id": new_v.id,
            "diff_length": 4
        })
        
        # Get changes by route (IN -> DE, Student)
        changes = await repo.get_by_route("IN", "DE", "Student")
        
        assert any(c.id == change1.id for c in changes)
        assert not any(c.source_id == source2.id for c in changes)
    
    async def test_get_by_date_range(self, db_session, sample_source_data):
        """Test getting policy changes by date range."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        version_repo = PolicyVersionRepository(db_session)
        repo = PolicyChangeRepository(db_session)
        
        now = datetime.utcnow()
        old_hash = generate_hash("old")
        new_hash = generate_hash("new")
        
        old_v = await version_repo.create({
            "source_id": source.id,
            "content_hash": old_hash,
            "raw_text": "old",
            "fetched_at": now - timedelta(days=2),
            "normalized_at": now - timedelta(days=2),
            "content_length": 3,
            "fetch_duration": 50
        })
        
        new_v = await version_repo.create({
            "source_id": source.id,
            "content_hash": new_hash,
            "raw_text": "new",
            "fetched_at": now,
            "normalized_at": now,
            "content_length": 3,
            "fetch_duration": 50
        })
        
        # Create change within range
        change1 = await repo.create({
            "source_id": source.id,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "diff": "diff",
            "detected_at": now - timedelta(days=1),
            "old_version_id": old_v.id,
            "new_version_id": new_v.id,
            "diff_length": 4
        })
        
        # Create change outside range
        change2 = await repo.create({
            "source_id": source.id,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "diff": "diff",
            "detected_at": now - timedelta(days=5),
            "old_version_id": old_v.id,
            "new_version_id": new_v.id,
            "diff_length": 4
        })
        
        # Get changes in date range
        start_date = now - timedelta(days=2)
        end_date = now
        changes = await repo.get_by_date_range(start_date, end_date)
        
        assert any(c.id == change1.id for c in changes)
        assert not any(c.id == change2.id for c in changes)




