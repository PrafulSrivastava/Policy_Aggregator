"""Integration tests for change detection in fetch pipeline."""

import pytest
from datetime import datetime
from api.services.version_storage import store_policy_version
from api.services.change_detector import detect_change
from api.services.normalizer import normalize
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.repositories.source_repository import SourceRepository
from api.utils.hashing import generate_hash


@pytest.mark.asyncio
class TestChangeDetectionIntegration:
    """Integration tests for change detection in fetch pipeline."""
    
    async def test_fetch_modify_fetch_detect_change(self, db_session, sample_source_data):
        """Test: fetch source, modify content slightly, fetch again, verify change detected."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Simulate first fetch
        raw_text1 = "Original policy content.\n\nSection 1: Requirements."
        normalized_text1 = normalize(raw_text1)
        fetched_at1 = datetime.utcnow()
        
        version1 = await store_policy_version(
            db_session,
            source.id,
            normalized_text1,
            fetched_at1
        )
        
        # Verify version1 stored
        assert version1 is not None
        hash1 = generate_hash(normalized_text1).lower()
        assert version1.content_hash == hash1
        
        # Simulate second fetch with modified content
        raw_text2 = "Original policy content.\n\nSection 1: Requirements.\n\nSection 2: New section added."
        normalized_text2 = normalize(raw_text2)
        fetched_at2 = datetime.utcnow()
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            normalized_text2,
            fetched_at2
        )
        
        # Verify version2 is different
        assert version2.id != version1.id
        hash2 = generate_hash(normalized_text2).lower()
        assert version2.content_hash == hash2
        assert hash2 != hash1
        
        # Test change detection on version2
        result = await detect_change(
            db_session,
            source.id,
            hash2,
            normalized_text2,
            version2.id
        )
        
        # Verify change was detected
        assert result.change_detected is True
        assert result.old_hash == hash1
        assert result.new_hash == hash2
        assert result.old_version_id == version1.id
        assert result.new_version_id == version2.id
        assert result.is_first_fetch is False
    
    async def test_fetch_twice_same_content_no_change(self, db_session, sample_source_data):
        """Test: fetch source twice with same content, verify no change detected."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Simulate first fetch
        raw_text = "Policy content here.\n\nMore content."
        normalized_text = normalize(raw_text)
        fetched_at1 = datetime.utcnow()
        
        version1 = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at1
        )
        
        # Simulate second fetch with same content
        # Note: store_policy_version is idempotent, so version2 will be same as version1
        # But for integration test, we want to test change detection logic
        # So we'll manually test detect_change with the same hash
        
        content_hash = generate_hash(normalized_text).lower()
        
        # Test change detection on version1 (should show no change since it's first)
        result = await detect_change(
            db_session,
            source.id,
            content_hash,
            normalized_text,
            version1.id
        )
        
        # For first version, should be first fetch
        assert result.change_detected is False
        assert result.is_first_fetch is True
        
        # Now create a second version manually (bypassing idempotency) to test same hash scenario
        version_repo = PolicyVersionRepository(db_session)
        fetched_at2 = datetime.utcnow()
        
        version2_data = {
            'source_id': source.id,
            'content_hash': content_hash,
            'raw_text': normalized_text,
            'fetched_at': fetched_at2,
            'normalized_at': fetched_at2,
            'content_length': len(normalized_text),
            'fetch_duration': 0
        }
        version2 = await version_repo.create(version2_data)
        
        # Test change detection on version2 (same hash as version1)
        result2 = await detect_change(
            db_session,
            source.id,
            content_hash,
            normalized_text,
            version2.id
        )
        
        # Should detect no change (same hash)
        assert result2.change_detected is False
        assert result2.old_hash == content_hash
        assert result2.new_hash == content_hash
        assert result2.old_version_id == version1.id
        assert result2.new_version_id == version2.id
        assert result2.is_first_fetch is False

