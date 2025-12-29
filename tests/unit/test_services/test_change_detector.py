"""Unit tests for change detection service."""

import pytest
import uuid
from datetime import datetime, timedelta
from api.services.change_detector import detect_change, ChangeDetectionResult
from api.services.version_storage import store_policy_version
from api.utils.hashing import generate_hash


@pytest.mark.asyncio
class TestChangeDetector:
    """Tests for change detection service."""
    
    async def test_same_hash_no_change_detected(self, db_session, sample_source_data):
        """Test that same hash results in no change detected."""
        from api.repositories.source_repository import SourceRepository
        from api.repositories.policy_version_repository import PolicyVersionRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "Same content for both versions."
        content_hash = generate_hash(normalized_text).lower()
        fetched_at1 = datetime.utcnow() - timedelta(hours=1)
        fetched_at2 = datetime.utcnow()
        
        # Manually create two versions with same hash to test change detection
        # (store_policy_version would return existing due to idempotency)
        repo = PolicyVersionRepository(db_session)
        
        version1_data = {
            'source_id': source.id,
            'content_hash': content_hash,
            'raw_text': normalized_text,
            'fetched_at': fetched_at1,
            'normalized_at': fetched_at1,
            'content_length': len(normalized_text),
            'fetch_duration': 0
        }
        version1 = await repo.create(version1_data)
        
        version2_data = {
            'source_id': source.id,
            'content_hash': content_hash,
            'raw_text': normalized_text,
            'fetched_at': fetched_at2,
            'normalized_at': fetched_at2,
            'content_length': len(normalized_text),
            'fetch_duration': 0
        }
        version2 = await repo.create(version2_data)
        
        # Test change detection on version2 (same hash as version1)
        result = await detect_change(
            db_session,
            source.id,
            content_hash,
            normalized_text,
            version2.id
        )
        
        assert result.change_detected is False
        assert result.new_hash == content_hash
        assert result.new_version_id == version2.id
        assert result.old_hash == content_hash
        assert result.old_version_id == version1.id
        assert result.is_first_fetch is False
        
    async def test_different_hash_change_detected(self, db_session, sample_source_data):
        """Test that different hash results in change detected."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        text1 = "First version of content."
        text2 = "Second version with different content."
        fetched_at1 = datetime.utcnow()
        
        # Store first version
        version1 = await store_policy_version(
            db_session,
            source.id,
            text1,
            fetched_at1
        )
        
        # Store different content (creates new version)
        fetched_at2 = datetime.utcnow()
        version2 = await store_policy_version(
            db_session,
            source.id,
            text2,
            fetched_at2
        )
        
        # Now test change detection on version2
        hash2 = generate_hash(text2).lower()
        result = await detect_change(
            db_session,
            source.id,
            hash2,
            text2,
            version2.id
        )
        
        assert result.change_detected is True
        assert result.new_hash == hash2
        assert result.new_version_id == version2.id
        assert result.old_hash == generate_hash(text1).lower()
        assert result.old_version_id == version1.id
        assert result.is_first_fetch is False
    
    async def test_first_fetch_no_change(self, db_session, sample_source_data):
        """Test first fetch scenario (no previous version)."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "First fetch for this source."
        fetched_at = datetime.utcnow()
        
        # Store first version
        version = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at
        )
        
        # Test change detection (should detect first fetch)
        content_hash = generate_hash(normalized_text).lower()
        result = await detect_change(
            db_session,
            source.id,
            content_hash,
            normalized_text,
            version.id
        )
        
        # For first fetch, we need to check before storing
        # Actually, after storing, there's one version, so it's not first fetch
        # Let me test it differently - call detect_change before any version exists
        
        # Create a new source for first fetch test
        source2 = await source_repo.create({
            **sample_source_data,
            "url": "https://example.com/another-source"
        })
        
        # Store first version for source2
        version2 = await store_policy_version(
            db_session,
            source2.id,
            normalized_text,
            fetched_at
        )
        
        # The detect_change is called automatically in store_policy_version
        # But for unit testing, let's test it directly
        # We need to test with a version that has no previous version
        # Actually, the logic in detect_change gets all versions and excludes current
        # So if there's only one version, previous_version will be None
        
        # Let's manually test the first fetch case
        # Create a version but don't commit, then test
        from api.repositories.policy_version_repository import PolicyVersionRepository
        
        repo = PolicyVersionRepository(db_session)
        # Get versions for a source with no versions
        source3 = await source_repo.create({
            **sample_source_data,
            "url": "https://example.com/third-source"
        })
        
        text3 = "Content for first fetch test."
        hash3 = generate_hash(text3).lower()
        
        # Create version manually to get ID
        version_data = {
            'source_id': source3.id,
            'content_hash': hash3,
            'raw_text': text3,
            'fetched_at': datetime.utcnow(),
            'normalized_at': datetime.utcnow(),
            'content_length': len(text3),
            'fetch_duration': 0
        }
        version3 = await repo.create(version_data)
        
        # Now test change detection - should detect first fetch
        result = await detect_change(
            db_session,
            source3.id,
            hash3,
            text3,
            version3.id
        )
        
        assert result.change_detected is False
        assert result.is_first_fetch is True
        assert result.new_hash == hash3
        assert result.new_version_id == version3.id
        assert result.old_hash is None
        assert result.old_version_id is None
    
    async def test_hash_comparison_deterministic(self, db_session, sample_source_data):
        """Test that hash comparison is deterministic (same content → same hash)."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        normalized_text = "Test content for deterministic hash."
        
        # Generate hash multiple times - should be same
        hash1 = generate_hash(normalized_text).lower()
        hash2 = generate_hash(normalized_text).lower()
        hash3 = generate_hash(normalized_text).lower()
        
        assert hash1 == hash2 == hash3, "Hash generation should be deterministic"
        
        # Test that hash comparison is fast (simple string comparison)
        import time
        start = time.time()
        comparison_result = (hash1 == hash2)
        elapsed = time.time() - start
        
        assert comparison_result is True
        assert elapsed < 0.001, "Hash comparison should be very fast (< 1ms)"
    
    async def test_source_with_previous_version(self, db_session, sample_source_data):
        """Test change detection for source with previous version."""
        from api.repositories.source_repository import SourceRepository
        
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        text1 = "Original content."
        text2 = "Updated content."
        fetched_at1 = datetime.utcnow() - timedelta(hours=1)
        fetched_at2 = datetime.utcnow()
        
        # Store first version
        version1 = await store_policy_version(
            db_session,
            source.id,
            text1,
            fetched_at1
        )
        
        # Store second version with different content
        version2 = await store_policy_version(
            db_session,
            source.id,
            text2,
            fetched_at2
        )
        
        # Test change detection on version2
        hash2 = generate_hash(text2).lower()
        result = await detect_change(
            db_session,
            source.id,
            hash2,
            text2,
            version2.id
        )
        
        assert result.change_detected is True
        assert result.old_version_id == version1.id
        assert result.new_version_id == version2.id
        assert result.is_first_fetch is False

