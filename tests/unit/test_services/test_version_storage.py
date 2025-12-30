"""Unit tests for version storage service."""

import pytest
import uuid
from datetime import datetime
from api.services.version_storage import (
    store_policy_version,
    get_latest_policy_version,
    get_policy_version_by_hash
)
from api.models.db.policy_version import PolicyVersion
from api.utils.hashing import generate_hash


@pytest.mark.asyncio
class TestStorePolicyVersion:
    """Tests for store_policy_version() function."""
    
    async def test_create_new_policy_version(self, db_session, sample_source_data):
        """Test creating a new PolicyVersion for new content."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "This is normalized policy content."
        fetched_at = datetime.utcnow()
        
        version = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at
        )
        
        assert version is not None
        assert version.source_id == source.id
        assert version.raw_text == normalized_text
        assert version.fetched_at == fetched_at
        assert version.content_hash == generate_hash(normalized_text).lower()
        assert version.content_length == len(normalized_text)
        assert version.normalized_at is not None
        assert version.fetch_duration == 0  # Default when not provided
    
    async def test_idempotency_duplicate_hash(self, db_session, sample_source_data):
        """Test that duplicate hash returns existing version (idempotency)."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "Same content for idempotency test."
        fetched_at = datetime.utcnow()
        
        # Store first version
        version1 = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at
        )
        
        # Store same content again (should return existing version)
        fetched_at2 = datetime.utcnow()
        version2 = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at2
        )
        
        # Should return the same version (idempotent)
        assert version1.id == version2.id
        assert version1.content_hash == version2.content_hash
        assert version1.raw_text == version2.raw_text
    
    async def test_different_content_creates_new_version(self, db_session, sample_source_data):
        """Test that different content creates new version."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        text1 = "First version of content."
        text2 = "Second version with different content."
        fetched_at = datetime.utcnow()
        
        # Store first version
        version1 = await store_policy_version(
            db_session,
            source.id,
            text1,
            fetched_at
        )
        
        # Store different content
        version2 = await store_policy_version(
            db_session,
            source.id,
            text2,
            fetched_at
        )
        
        # Should create different versions
        assert version1.id != version2.id
        assert version1.content_hash != version2.content_hash
        assert version1.raw_text != version2.raw_text
    
    async def test_stores_full_text_content(self, db_session, sample_source_data):
        """Test that full text content is stored (not just hash)."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "This is the full text content that should be stored."
        fetched_at = datetime.utcnow()
        
        version = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at
        )
        
        # Verify full text is stored
        assert version.raw_text == normalized_text
        assert len(version.raw_text) > 0
        assert version.content_length == len(normalized_text)
    
    async def test_generates_correct_hash(self, db_session, sample_source_data):
        """Test that correct SHA256 hash is generated."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "Test content for hash generation."
        fetched_at = datetime.utcnow()
        
        version = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at
        )
        
        # Verify hash is correct
        expected_hash = generate_hash(normalized_text).lower()
        assert version.content_hash == expected_hash
        assert len(version.content_hash) == 64
    
    async def test_fetch_duration_from_metadata(self, db_session, sample_source_data):
        """Test that fetch_duration is extracted from metadata."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "Test content."
        fetched_at = datetime.utcnow()
        fetch_metadata = {'fetch_duration': 150}  # 150ms
        
        version = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at,
            fetch_metadata
        )
        
        assert version.fetch_duration == 150
    
    async def test_empty_text_raises_error(self, db_session, sample_source_data):
        """Test that empty text raises ValueError."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        with pytest.raises(ValueError, match="cannot be empty"):
            await store_policy_version(
                db_session,
                source.id,
                "",
                datetime.utcnow()
            )
    
    async def test_whitespace_only_text_raises_error(self, db_session, sample_source_data):
        """Test that whitespace-only text raises ValueError."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        with pytest.raises(ValueError, match="cannot be empty"):
            await store_policy_version(
                db_session,
                source.id,
                "   \n\n   ",
                datetime.utcnow()
            )
    
    async def test_immutability_no_update(self, db_session, sample_source_data):
        """Test that PolicyVersion is never updated (immutability)."""
        from api.repositories.source_repository import SourceRepository
        from api.repositories.policy_version_repository import PolicyVersionRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "Original content."
        fetched_at = datetime.utcnow()
        
        # Store version
        version1 = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at
        )
        
        original_id = version1.id
        original_created_at = version1.created_at
        
        # Try to store same content again (should return existing, not update)
        version2 = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            datetime.utcnow()  # Different fetched_at
        )
        
        # Should be same version (idempotent)
        assert version1.id == version2.id
        assert version1.created_at == version2.created_at
        
        # Verify no update occurred
        repo = PolicyVersionRepository(db_session)
        retrieved = await repo.get_by_id(original_id)
        assert retrieved.created_at == original_created_at


@pytest.mark.asyncio
class TestGetLatestPolicyVersion:
    """Tests for get_latest_policy_version() function."""
    
    async def test_get_latest_version(self, db_session, sample_source_data):
        """Test getting latest PolicyVersion for a source."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Store multiple versions
        version1 = await store_policy_version(
            db_session,
            source.id,
            "First version.",
            datetime.utcnow()
        )
        
        # Wait a bit to ensure different timestamps
        import asyncio
        await asyncio.sleep(0.01)
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            "Second version.",
            datetime.utcnow()
        )
        
        # Get latest
        latest = await get_latest_policy_version(db_session, source.id)
        
        assert latest is not None
        assert latest.id == version2.id  # Should be the most recent
        assert latest.raw_text == "Second version."
    
    async def test_get_latest_no_versions(self, db_session, sample_source_data):
        """Test getting latest when no versions exist."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Get latest (no versions exist)
        latest = await get_latest_policy_version(db_session, source.id)
        
        assert latest is None


@pytest.mark.asyncio
class TestGetPolicyVersionByHash:
    """Tests for get_policy_version_by_hash() function."""
    
    async def test_get_by_hash(self, db_session, sample_source_data):
        """Test getting PolicyVersion by hash."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "Content for hash lookup."
        fetched_at = datetime.utcnow()
        
        # Store version
        version = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at
        )
        
        # Get by hash
        retrieved = await get_policy_version_by_hash(
            db_session,
            version.content_hash
        )
        
        assert retrieved is not None
        assert retrieved.id == version.id
        assert retrieved.content_hash == version.content_hash
    
    async def test_get_by_hash_not_found(self, db_session):
        """Test getting PolicyVersion by non-existent hash."""
        fake_hash = "a" * 64  # Valid format but doesn't exist
        
        retrieved = await get_policy_version_by_hash(db_session, fake_hash)
        
        assert retrieved is None
    
    async def test_get_by_hash_case_insensitive(self, db_session, sample_source_data):
        """Test that hash lookup is case-insensitive."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "Content for case test."
        fetched_at = datetime.utcnow()
        
        # Store version
        version = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at
        )
        
        # Get by hash with uppercase
        uppercase_hash = version.content_hash.upper()
        retrieved = await get_policy_version_by_hash(db_session, uppercase_hash)
        
        assert retrieved is not None
        assert retrieved.id == version.id




