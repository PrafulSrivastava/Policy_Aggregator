"""Integration tests for version storage in fetch pipeline."""

import pytest
from datetime import datetime
from api.services.version_storage import store_policy_version
from api.services.normalizer import normalize
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.repositories.source_repository import SourceRepository


@pytest.mark.asyncio
class TestVersionStorageIntegration:
    """Integration tests for version storage in fetch pipeline."""
    
    async def test_fetch_same_source_twice_unchanged_content(self, db_session, sample_source_data):
        """Test: fetch same source twice with unchanged content, verify only one version created."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Simulate fetch and normalization
        raw_text = "Policy content here.\n\nMore content."
        normalized_text = normalize(raw_text)
        fetched_at1 = datetime.utcnow()
        
        # Store first version
        version1 = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at1
        )
        
        # Simulate second fetch with same content
        fetched_at2 = datetime.utcnow()
        version2 = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at2
        )
        
        # Verify only one version exists (idempotent)
        assert version1.id == version2.id
        assert version1.content_hash == version2.content_hash
        
        # Verify only one version in database
        version_repo = PolicyVersionRepository(db_session)
        all_versions = await version_repo.get_by_source_id(source.id)
        assert len(all_versions) == 1
    
    async def test_fetch_same_source_twice_changed_content(self, db_session, sample_source_data):
        """Test: fetch same source with changed content, verify two versions created."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Simulate first fetch
        raw_text1 = "Original policy content."
        normalized_text1 = normalize(raw_text1)
        fetched_at1 = datetime.utcnow()
        
        version1 = await store_policy_version(
            db_session,
            source.id,
            normalized_text1,
            fetched_at1
        )
        
        # Simulate second fetch with changed content
        raw_text2 = "Updated policy content with changes."
        normalized_text2 = normalize(raw_text2)
        fetched_at2 = datetime.utcnow()
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            normalized_text2,
            fetched_at2
        )
        
        # Verify two different versions created
        assert version1.id != version2.id
        assert version1.content_hash != version2.content_hash
        assert version1.raw_text != version2.raw_text
        
        # Verify both versions in database
        version_repo = PolicyVersionRepository(db_session)
        all_versions = await version_repo.get_by_source_id(source.id)
        assert len(all_versions) == 2
        
        # Verify latest is version2
        latest = await version_repo.get_latest_by_source_id(source.id)
        assert latest.id == version2.id
    
    async def test_full_pipeline_fetch_normalize_store(self, db_session, sample_source_data):
        """Test full pipeline: fetch → normalize → store."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Simulate fetch result (with formatting issues)
        raw_text = "  Policy Title    \r\n\r\n  Copyright © 2024  \r\n  \r\n  Section 1: Content here.    \r\n  \r\n  Section 2: More content.  \r\n  \r\n  Last updated: 2024-01-27  \r\n"
        
        # Normalize
        normalized_text = normalize(raw_text)
        
        # Store version
        fetched_at = datetime.utcnow()
        version = await store_policy_version(
            db_session,
            source.id,
            normalized_text,
            fetched_at,
            {'fetch_duration': 250}
        )
        
        # Verify version stored correctly
        assert version is not None
        assert version.source_id == source.id
        assert version.raw_text == normalized_text
        assert version.content_length == len(normalized_text)
        assert version.fetch_duration == 250
        
        # Verify normalized text doesn't have formatting issues
        assert "  Policy Title" not in version.raw_text  # Leading spaces removed
        assert "Copyright" not in version.raw_text  # Boilerplate removed
        assert "Last updated" not in version.raw_text  # Boilerplate removed
        assert "Section 1: Content here." in version.raw_text  # Content preserved
        assert "Section 2: More content." in version.raw_text  # Content preserved
    
    async def test_idempotency_with_normalization(self, db_session, sample_source_data):
        """Test idempotency when same content is normalized and stored multiple times."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Same raw text with different formatting
        raw_text1 = "  Content here.    \r\n  More content.  "
        raw_text2 = "Content here.\nMore content."  # Different formatting, same content
        
        # Normalize both (should produce same normalized text)
        normalized_text1 = normalize(raw_text1)
        normalized_text2 = normalize(raw_text2)
        
        # Should produce same normalized text
        assert normalized_text1 == normalized_text2
        
        # Store first version
        version1 = await store_policy_version(
            db_session,
            source.id,
            normalized_text1,
            datetime.utcnow()
        )
        
        # Store second version (same normalized content)
        version2 = await store_policy_version(
            db_session,
            source.id,
            normalized_text2,
            datetime.utcnow()
        )
        
        # Should return same version (idempotent)
        assert version1.id == version2.id
        
        # Verify only one version in database
        version_repo = PolicyVersionRepository(db_session)
        all_versions = await version_repo.get_by_source_id(source.id)
        assert len(all_versions) == 1



