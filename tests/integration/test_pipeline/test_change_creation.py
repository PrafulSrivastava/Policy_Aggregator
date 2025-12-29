"""Integration tests for PolicyChange creation in fetch pipeline."""

import pytest
from datetime import datetime
from api.services.version_storage import store_policy_version
from api.services.normalizer import normalize
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.source_repository import SourceRepository
from api.utils.hashing import generate_hash


@pytest.mark.asyncio
class TestChangeCreationIntegration:
    """Integration tests for PolicyChange creation in fetch pipeline."""
    
    async def test_full_flow_fetch_change_detected_policychange_created(
        self,
        db_session,
        sample_source_data
    ):
        """Test full flow: fetch → change detected → diff generated → PolicyChange created."""
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
        
        # Verify first version stored (no PolicyChange created for first fetch)
        change_repo = PolicyChangeRepository(db_session)
        changes_after_first = await change_repo.get_by_source_id(source.id)
        assert len(changes_after_first) == 0  # No change for first fetch
        
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
        
        # Verify versions are different
        assert version2.id != version1.id
        assert version2.content_hash != version1.content_hash
        
        # Verify PolicyChange was created automatically
        changes_after_second = await change_repo.get_by_source_id(source.id)
        assert len(changes_after_second) == 1
        
        policy_change = changes_after_second[0]
        
        # Verify PolicyChange has all required fields
        assert policy_change is not None
        assert policy_change.source_id == source.id
        assert policy_change.old_version_id == version1.id
        assert policy_change.new_version_id == version2.id
        assert policy_change.old_hash == generate_hash(normalized_text1).lower()
        assert policy_change.new_hash == generate_hash(normalized_text2).lower()
        assert policy_change.diff is not None
        assert len(policy_change.diff) > 0
        assert policy_change.diff_length == len(policy_change.diff)
        assert policy_change.detected_at is not None
    
    async def test_policychange_links_to_correct_versions(
        self,
        db_session,
        sample_source_data
    ):
        """Test that PolicyChange links to correct PolicyVersions."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create three versions
        text1 = "Version 1 content."
        text2 = "Version 2 content."
        text3 = "Version 3 content."
        
        version1 = await store_policy_version(
            db_session,
            source.id,
            text1,
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            text2,
            datetime.utcnow()
        )
        
        version3 = await store_policy_version(
            db_session,
            source.id,
            text3,
            datetime.utcnow()
        )
        
        # Verify two PolicyChanges created (v1→v2 and v2→v3)
        change_repo = PolicyChangeRepository(db_session)
        changes = await change_repo.get_by_source_id(source.id)
        
        assert len(changes) == 2
        
        # Find changes by version IDs
        change1 = next((c for c in changes if c.old_version_id == version1.id), None)
        change2 = next((c for c in changes if c.old_version_id == version2.id), None)
        
        assert change1 is not None
        assert change2 is not None
        
        # Verify links
        assert change1.old_version_id == version1.id
        assert change1.new_version_id == version2.id
        assert change2.old_version_id == version2.id
        assert change2.new_version_id == version3.id
    
    async def test_policychange_has_correct_hashes(self, db_session, sample_source_data):
        """Test that PolicyChange stores correct hashes."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create versions
        text1 = "Original text."
        text2 = "Modified text."
        
        version1 = await store_policy_version(
            db_session,
            source.id,
            text1,
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            text2,
            datetime.utcnow()
        )
        
        # Verify PolicyChange has correct hashes
        change_repo = PolicyChangeRepository(db_session)
        changes = await change_repo.get_by_source_id(source.id)
        
        assert len(changes) == 1
        policy_change = changes[0]
        
        expected_old_hash = generate_hash(text1).lower()
        expected_new_hash = generate_hash(text2).lower()
        
        assert policy_change.old_hash == expected_old_hash
        assert policy_change.new_hash == expected_new_hash
    
    async def test_policychange_stores_diff(self, db_session, sample_source_data):
        """Test that PolicyChange stores the diff correctly."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create versions with clear changes
        text1 = "Line 1: Original.\nLine 2: Unchanged.\nLine 3: To remove."
        text2 = "Line 1: Original.\nLine 2: Unchanged.\nLine 3: Modified.\nLine 4: Added."
        
        version1 = await store_policy_version(
            db_session,
            source.id,
            text1,
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            text2,
            datetime.utcnow()
        )
        
        # Verify PolicyChange has diff
        change_repo = PolicyChangeRepository(db_session)
        changes = await change_repo.get_by_source_id(source.id)
        
        assert len(changes) == 1
        policy_change = changes[0]
        
        # Verify diff is stored
        assert policy_change.diff is not None
        assert len(policy_change.diff) > 0
        assert policy_change.diff_length == len(policy_change.diff)
        
        # Verify diff contains change markers (unified diff format)
        assert "---" in policy_change.diff or "+++" in policy_change.diff or "@@" in policy_change.diff
    
    async def test_multiple_changes_create_multiple_records(self, db_session, sample_source_data):
        """Test that multiple changes create multiple PolicyChange records."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create multiple versions
        versions = []
        for i in range(1, 5):
            text = f"Version {i} content."
            version = await store_policy_version(
                db_session,
                source.id,
                text,
                datetime.utcnow()
            )
            versions.append(version)
        
        # Verify multiple PolicyChanges created
        change_repo = PolicyChangeRepository(db_session)
        changes = await change_repo.get_by_source_id(source.id)
        
        # Should have 3 changes (v1→v2, v2→v3, v3→v4)
        assert len(changes) == 3
        
        # Verify all are separate records
        change_ids = [c.id for c in changes]
        assert len(change_ids) == len(set(change_ids))  # All unique IDs
        
        # Verify chronological order (latest first)
        for i in range(len(changes) - 1):
            assert changes[i].detected_at >= changes[i + 1].detected_at

