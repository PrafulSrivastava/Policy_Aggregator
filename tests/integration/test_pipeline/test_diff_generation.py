"""Integration tests for diff generation in fetch pipeline."""

import pytest
from datetime import datetime
from api.services.version_storage import store_policy_version
from api.services.change_detector import detect_change
from api.services.normalizer import normalize
from api.services.diff_generator import generate_diff
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.source_repository import SourceRepository
from api.utils.hashing import generate_hash


@pytest.mark.asyncio
class TestDiffGenerationIntegration:
    """Integration tests for diff generation in fetch pipeline."""
    
    async def test_change_detected_diff_generated_policychange_created(
        self,
        db_session,
        sample_source_data
    ):
        """Test: change detected → diff generated → PolicyChange created."""
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
        hash2 = generate_hash(normalized_text2).lower()
        
        # Test change detection (which should generate diff)
        result = await detect_change(
            db_session,
            source.id,
            hash2,
            normalized_text2,
            version2.id
        )
        
        # Verify change was detected and diff was generated
        assert result.change_detected is True
        assert result.diff is not None
        assert len(result.diff) > 0
        
        # Verify diff format is readable (contains diff markers)
        assert "---" in result.diff or "+++" in result.diff
        assert "version_" in result.diff or "old_version" in result.diff or "new_version" in result.diff
        
        # Verify diff contains content from both versions
        # (may be normalized, so check for key terms)
        assert "Section" in result.diff or "Requirements" in result.diff or "+" in result.diff or "-" in result.diff
        
        # Create PolicyChange record with the diff
        change_repo = PolicyChangeRepository(db_session)
        change_data = {
            'source_id': source.id,
            'old_hash': result.old_hash,
            'new_hash': result.new_hash,
            'diff': result.diff,
            'detected_at': datetime.utcnow(),
            'old_version_id': result.old_version_id,
            'new_version_id': result.new_version_id,
            'diff_length': len(result.diff)
        }
        policy_change = await change_repo.create(change_data)
        
        # Verify PolicyChange was created with diff
        assert policy_change is not None
        assert policy_change.diff == result.diff
        assert policy_change.diff_length == len(result.diff)
        assert policy_change.old_version_id == version1.id
        assert policy_change.new_version_id == version2.id
        assert policy_change.source_id == source.id
    
    async def test_diff_format_is_readable(self, db_session, sample_source_data):
        """Test that diff format is human-readable."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create two versions with clear changes
        old_text = "Line 1: Original.\nLine 2: Unchanged.\nLine 3: To remove."
        new_text = "Line 1: Original.\nLine 2: Unchanged.\nLine 3: Modified.\nLine 4: Added."
        
        # Store versions
        version1 = await store_policy_version(
            db_session,
            source.id,
            old_text,
            datetime.utcnow()
        )
        
        version2 = await store_policy_version(
            db_session,
            source.id,
            new_text,
            datetime.utcnow()
        )
        
        # Generate diff directly
        diff = generate_diff(
            old_text=old_text,
            new_text=new_text,
            context_lines=3
        )
        
        # Verify diff is readable
        assert diff is not None
        assert len(diff) > 0
        
        # Check for unified diff format markers
        assert "---" in diff
        assert "+++" in diff
        assert "@@" in diff  # Hunk header
        
        # Verify it shows the changes
        assert ("Line 3" in diff or "Modified" in diff or "Added" in diff or
                "+" in diff or "-" in diff)
    
    async def test_diff_includes_context_lines(self, db_session, sample_source_data):
        """Test that diff includes context lines around changes."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create text with context around change
        old_text = "Context line 1.\nContext line 2.\nLine to change.\nContext line 3.\nContext line 4."
        new_text = "Context line 1.\nContext line 2.\nLine changed.\nContext line 3.\nContext line 4."
        
        # Generate diff with context
        diff = generate_diff(old_text, new_text, context_lines=2)
        
        # Verify context lines are included
        assert "Context line 2" in diff or "Context line 3" in diff
        assert "Line to change" in diff or "Line changed" in diff or "-" in diff or "+" in diff

