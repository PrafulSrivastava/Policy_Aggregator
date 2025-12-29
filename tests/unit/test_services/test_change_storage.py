"""Unit tests for change storage service."""

import pytest
import uuid
from datetime import datetime
from api.services.change_storage import create_policy_change
from api.services.version_storage import store_policy_version
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.source_repository import SourceRepository
from api.utils.hashing import generate_hash


@pytest.mark.asyncio
class TestCreatePolicyChange:
    """Tests for create_policy_change() function."""
    
    async def test_create_policy_change_with_all_fields(self, db_session, sample_source_data):
        """Test creating PolicyChange with all required fields."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create two versions
        text1 = "Original content."
        text2 = "Modified content."
        fetched_at1 = datetime.utcnow()
        fetched_at2 = datetime.utcnow()
        
        version1 = await store_policy_version(
            db_session,
            source.id,
            text1,
            fetched_at1
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            text2,
            fetched_at2
        )
        
        # Create PolicyChange
        old_hash = generate_hash(text1).lower()
        new_hash = generate_hash(text2).lower()
        diff = f"--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Original content.\n+Modified content.\n"
        detected_at = datetime.utcnow()
        
        policy_change = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version1.id,
            new_version_id=version2.id,
            old_hash=old_hash,
            new_hash=new_hash,
            diff=diff,
            detected_at=detected_at
        )
        
        # Verify PolicyChange was created
        assert policy_change is not None
        assert policy_change.source_id == source.id
        assert policy_change.old_version_id == version1.id
        assert policy_change.new_version_id == version2.id
        assert policy_change.old_hash == old_hash
        assert policy_change.new_hash == new_hash
        assert policy_change.diff == diff
        assert policy_change.diff_length == len(diff)
        assert policy_change.detected_at == detected_at
    
    async def test_links_to_old_and_new_policy_versions(self, db_session, sample_source_data):
        """Test that PolicyChange links to both old and new PolicyVersions."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create versions
        version1 = await store_policy_version(
            db_session,
            source.id,
            "Text 1",
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            "Text 2",
            datetime.utcnow()
        )
        
        # Create PolicyChange
        old_hash = generate_hash("Text 1").lower()
        new_hash = generate_hash("Text 2").lower()
        diff = "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Text 1\n+Text 2\n"
        
        policy_change = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version1.id,
            new_version_id=version2.id,
            old_hash=old_hash,
            new_hash=new_hash,
            diff=diff,
            detected_at=datetime.utcnow()
        )
        
        # Verify links to versions
        assert policy_change.old_version_id == version1.id
        assert policy_change.new_version_id == version2.id
        
        # Verify relationships work
        change_repo = PolicyChangeRepository(db_session)
        retrieved = await change_repo.get_by_id(policy_change.id)
        assert retrieved is not None
        assert retrieved.old_version_id == version1.id
        assert retrieved.new_version_id == version2.id
    
    async def test_stores_diff_correctly(self, db_session, sample_source_data):
        """Test that diff is stored correctly."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create versions
        version1 = await store_policy_version(
            db_session,
            source.id,
            "Old text",
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            "New text",
            datetime.utcnow()
        )
        
        # Create PolicyChange with specific diff
        diff_text = "--- version_old\n+++ version_new\n@@ -1,1 +1,1 @@\n-Old text\n+New text\n"
        
        policy_change = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version1.id,
            new_version_id=version2.id,
            old_hash=generate_hash("Old text").lower(),
            new_hash=generate_hash("New text").lower(),
            diff=diff_text,
            detected_at=datetime.utcnow()
        )
        
        # Verify diff stored correctly
        assert policy_change.diff == diff_text
        assert policy_change.diff_length == len(diff_text)
    
    async def test_calculates_diff_length(self, db_session, sample_source_data):
        """Test that diff_length is calculated correctly."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create versions
        version1 = await store_policy_version(
            db_session,
            source.id,
            "Short",
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            "Longer text with more content",
            datetime.utcnow()
        )
        
        # Create PolicyChange with known diff length
        diff_text = "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Short\n+Longer text with more content\n"
        expected_length = len(diff_text)
        
        policy_change = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version1.id,
            new_version_id=version2.id,
            old_hash=generate_hash("Short").lower(),
            new_hash=generate_hash("Longer text with more content").lower(),
            diff=diff_text,
            detected_at=datetime.utcnow()
        )
        
        # Verify diff_length is correct
        assert policy_change.diff_length == expected_length
    
    async def test_immutability_new_changes_always_created(self, db_session, sample_source_data):
        """Test that PolicyChange records are immutable - new changes always create new records."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create versions
        version1 = await store_policy_version(
            db_session,
            source.id,
            "Version 1",
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            "Version 2",
            datetime.utcnow()
        )
        
        version3 = await store_policy_version(
            db_session,
            source.id,
            "Version 3",
            datetime.utcnow()
        )
        
        # Create first PolicyChange
        diff1 = "--- v1\n+++ v2\n@@ -1,1 +1,1 @@\n-Version 1\n+Version 2\n"
        change1 = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version1.id,
            new_version_id=version2.id,
            old_hash=generate_hash("Version 1").lower(),
            new_hash=generate_hash("Version 2").lower(),
            diff=diff1,
            detected_at=datetime.utcnow()
        )
        
        # Create second PolicyChange (should be new record, not update)
        diff2 = "--- v2\n+++ v3\n@@ -1,1 +1,1 @@\n-Version 2\n+Version 3\n"
        change2 = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version2.id,
            new_version_id=version3.id,
            old_hash=generate_hash("Version 2").lower(),
            new_hash=generate_hash("Version 3").lower(),
            diff=diff2,
            detected_at=datetime.utcnow()
        )
        
        # Verify both are separate records
        assert change1.id != change2.id
        assert change1.new_version_id == version2.id
        assert change2.old_version_id == version2.id
        assert change2.new_version_id == version3.id
    
    async def test_validates_required_fields(self, db_session, sample_source_data):
        """Test that validation errors are raised for invalid fields."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create versions
        version1 = await store_policy_version(
            db_session,
            source.id,
            "Text 1",
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            "Text 2",
            datetime.utcnow()
        )
        
        old_hash = generate_hash("Text 1").lower()
        new_hash = generate_hash("Text 2").lower()
        diff = "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Text 1\n+Text 2\n"
        
        # Test invalid source_id
        with pytest.raises(ValueError, match="source_id cannot be None"):
            await create_policy_change(
                session=db_session,
                source_id=None,  # type: ignore
                old_version_id=version1.id,
                new_version_id=version2.id,
                old_hash=old_hash,
                new_hash=new_hash,
                diff=diff,
                detected_at=datetime.utcnow()
            )
        
        # Test invalid hash length
        with pytest.raises(ValueError, match="old_hash must be 64 characters"):
            await create_policy_change(
                session=db_session,
                source_id=source.id,
                old_version_id=version1.id,
                new_version_id=version2.id,
                old_hash="short",
                new_hash=new_hash,
                diff=diff,
                detected_at=datetime.utcnow()
            )
        
        # Test same hash
        with pytest.raises(ValueError, match="old_hash and new_hash must be different"):
            await create_policy_change(
                session=db_session,
                source_id=source.id,
                old_version_id=version1.id,
                new_version_id=version2.id,
                old_hash=old_hash,
                new_hash=old_hash,  # Same hash
                diff=diff,
                detected_at=datetime.utcnow()
            )
        
        # Test empty diff
        with pytest.raises(ValueError, match="diff cannot be empty"):
            await create_policy_change(
                session=db_session,
                source_id=source.id,
                old_version_id=version1.id,
                new_version_id=version2.id,
                old_hash=old_hash,
                new_hash=new_hash,
                diff="",
                detected_at=datetime.utcnow()
            )


@pytest.mark.asyncio
class TestHelperFunctions:
    """Tests for repository helper functions."""
    
    async def test_get_by_source_id(self, db_session, sample_source_data):
        """Test getting all changes for a source."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create versions and changes
        version1 = await store_policy_version(
            db_session,
            source.id,
            "V1",
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            "V2",
            datetime.utcnow()
        )
        
        version3 = await store_policy_version(
            db_session,
            source.id,
            "V3",
            datetime.utcnow()
        )
        
        # Create two PolicyChanges
        change1 = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version1.id,
            new_version_id=version2.id,
            old_hash=generate_hash("V1").lower(),
            new_hash=generate_hash("V2").lower(),
            diff="diff1",
            detected_at=datetime.utcnow()
        )
        
        change2 = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version2.id,
            new_version_id=version3.id,
            old_hash=generate_hash("V2").lower(),
            new_hash=generate_hash("V3").lower(),
            diff="diff2",
            detected_at=datetime.utcnow()
        )
        
        # Get all changes for source
        change_repo = PolicyChangeRepository(db_session)
        changes = await change_repo.get_by_source_id(source.id)
        
        # Verify both changes returned
        assert len(changes) == 2
        change_ids = [c.id for c in changes]
        assert change1.id in change_ids
        assert change2.id in change_ids
    
    async def test_get_by_date_range(self, db_session, sample_source_data):
        """Test getting changes within date range."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create versions
        version1 = await store_policy_version(
            db_session,
            source.id,
            "V1",
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            "V2",
            datetime.utcnow()
        )
        
        # Create change with specific date
        from datetime import timedelta
        now = datetime.utcnow()
        change_date = now - timedelta(days=5)
        
        change = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version1.id,
            new_version_id=version2.id,
            old_hash=generate_hash("V1").lower(),
            new_hash=generate_hash("V2").lower(),
            diff="diff",
            detected_at=change_date
        )
        
        # Get changes in date range
        change_repo = PolicyChangeRepository(db_session)
        start_date = now - timedelta(days=10)
        end_date = now - timedelta(days=1)
        
        changes = await change_repo.get_by_date_range(start_date, end_date)
        
        # Verify change is in range
        assert len(changes) >= 1
        assert any(c.id == change.id for c in changes)
    
    async def test_get_latest_by_source_id(self, db_session, sample_source_data):
        """Test getting latest change for a source."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create versions
        version1 = await store_policy_version(
            db_session,
            source.id,
            "V1",
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            "V2",
            datetime.utcnow()
        )
        
        version3 = await store_policy_version(
            db_session,
            source.id,
            "V3",
            datetime.utcnow()
        )
        
        # Create two changes with different timestamps
        from datetime import timedelta
        now = datetime.utcnow()
        
        change1 = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version1.id,
            new_version_id=version2.id,
            old_hash=generate_hash("V1").lower(),
            new_hash=generate_hash("V2").lower(),
            diff="diff1",
            detected_at=now - timedelta(hours=2)
        )
        
        change2 = await create_policy_change(
            session=db_session,
            source_id=source.id,
            old_version_id=version2.id,
            new_version_id=version3.id,
            old_hash=generate_hash("V2").lower(),
            new_hash=generate_hash("V3").lower(),
            diff="diff2",
            detected_at=now
        )
        
        # Get latest change
        change_repo = PolicyChangeRepository(db_session)
        latest = await change_repo.get_latest_by_source_id(source.id)
        
        # Verify latest is change2
        assert latest is not None
        assert latest.id == change2.id

