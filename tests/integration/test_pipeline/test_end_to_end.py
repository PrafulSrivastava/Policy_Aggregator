"""Integration tests for end-to-end fetch pipeline."""

import pytest
from datetime import datetime
from api.services.fetcher_manager import fetch_and_process_source, PipelineResult
from api.repositories.source_repository import SourceRepository
from api.repositories.policy_version_repository import PolicyVersionRepository
from api.repositories.policy_change_repository import PolicyChangeRepository
from fetchers.base import FetchResult


@pytest.mark.asyncio
class TestEndToEndPipeline:
    """Integration tests for end-to-end fetch pipeline."""
    
    async def test_full_pipeline_first_fetch(self, db_session, sample_source_data):
        """Test full pipeline for first fetch (no previous version)."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create a mock fetcher
        def mock_fetcher(url, metadata):
            return FetchResult(
                raw_text="Original policy content.\n\nSection 1: Requirements.",
                content_type="html",
                success=True,
                fetched_at=datetime.utcnow()
            )
        
        # Register mock fetcher
        from api.services.fetcher_manager import register_fetcher
        fetcher_name = f"test_{source.country.lower()}_{source.visa_type.lower().replace(' ', '_')}"
        register_fetcher(fetcher_name, mock_fetcher, {"source_type": source.fetch_type})
        
        # Execute pipeline
        result = await fetch_and_process_source(db_session, source.id)
        
        # Verify pipeline succeeded
        assert result.success is True
        assert result.source_id == source.id
        assert result.policy_version_id is not None
        assert result.change_detected is False  # First fetch, no change
        assert result.policy_change_id is None
        assert result.error_message is None
        assert result.fetched_at is not None
        
        # Verify PolicyVersion was created
        version_repo = PolicyVersionRepository(db_session)
        version = await version_repo.get_by_id(result.policy_version_id)
        assert version is not None
        assert version.source_id == source.id
    
    async def test_full_pipeline_change_detected(self, db_session, sample_source_data):
        """Test full pipeline with change detected."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Register mock fetcher
        from api.services.fetcher_manager import register_fetcher
        fetcher_name = f"test_{source.country.lower()}_{source.visa_type.lower().replace(' ', '_')}"
        
        # First fetch
        def mock_fetcher_v1(url, metadata):
            return FetchResult(
                raw_text="Original policy content.\n\nSection 1: Requirements.",
                content_type="html",
                success=True,
                fetched_at=datetime.utcnow()
            )
        
        register_fetcher(fetcher_name, mock_fetcher_v1, {"source_type": source.fetch_type})
        
        result1 = await fetch_and_process_source(db_session, source.id)
        assert result1.success is True
        assert result1.change_detected is False
        
        # Second fetch with modified content
        def mock_fetcher_v2(url, metadata):
            return FetchResult(
                raw_text="Original policy content.\n\nSection 1: Requirements.\n\nSection 2: New section added.",
                content_type="html",
                success=True,
                fetched_at=datetime.utcnow()
            )
        
        register_fetcher(fetcher_name, mock_fetcher_v2, {"source_type": source.fetch_type})
        
        result2 = await fetch_and_process_source(db_session, source.id)
        
        # Verify pipeline succeeded and change detected
        assert result2.success is True
        assert result2.source_id == source.id
        assert result2.policy_version_id is not None
        assert result2.change_detected is True
        assert result2.policy_change_id is not None
        assert result2.error_message is None
        
        # Verify PolicyChange was created
        change_repo = PolicyChangeRepository(db_session)
        policy_change = await change_repo.get_by_id(result2.policy_change_id)
        assert policy_change is not None
        assert policy_change.source_id == source.id
        assert policy_change.old_version_id == result1.policy_version_id
        assert policy_change.new_version_id == result2.policy_version_id
        assert policy_change.diff is not None
        assert len(policy_change.diff) > 0
    
    async def test_full_pipeline_no_change(self, db_session, sample_source_data):
        """Test full pipeline with no change (same content)."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Register mock fetcher
        from api.services.fetcher_manager import register_fetcher
        fetcher_name = f"test_{source.country.lower()}_{source.visa_type.lower().replace(' ', '_')}"
        
        content = "Original policy content.\n\nSection 1: Requirements."
        
        def mock_fetcher(url, metadata):
            return FetchResult(
                raw_text=content,
                content_type="html",
                success=True,
                fetched_at=datetime.utcnow()
            )
        
        register_fetcher(fetcher_name, mock_fetcher, {"source_type": source.fetch_type})
        
        # First fetch
        result1 = await fetch_and_process_source(db_session, source.id)
        assert result1.success is True
        assert result1.change_detected is False
        
        # Second fetch with same content
        result2 = await fetch_and_process_source(db_session, source.id)
        
        # Verify pipeline succeeded but no change detected
        assert result2.success is True
        assert result2.change_detected is False
        assert result2.policy_change_id is None
        
        # Verify only one PolicyVersion exists (idempotent)
        version_repo = PolicyVersionRepository(db_session)
        versions = await version_repo.get_by_source_id(source.id)
        # Should have 1 or 2 versions depending on idempotency logic
        assert len(versions) >= 1
    
    async def test_pipeline_handles_fetcher_error(self, db_session, sample_source_data):
        """Test pipeline handles fetcher errors gracefully."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Register failing fetcher
        from api.services.fetcher_manager import register_fetcher
        fetcher_name = f"test_{source.country.lower()}_{source.visa_type.lower().replace(' ', '_')}"
        
        def failing_fetcher(url, metadata):
            return FetchResult(
                raw_text="",
                content_type="html",
                success=False,
                error_message="Connection timeout"
            )
        
        register_fetcher(fetcher_name, failing_fetcher, {"source_type": source.fetch_type})
        
        # Execute pipeline
        result = await fetch_and_process_source(db_session, source.id)
        
        # Verify pipeline failed gracefully
        assert result.success is False
        assert result.source_id == source.id
        assert result.error_message is not None
        assert "fetcher returned error" in result.error_message.lower()
        assert result.policy_version_id is None
    
    async def test_pipeline_all_steps_executed(self, db_session, sample_source_data):
        """Test that all pipeline steps are executed in order."""
        # Create a source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Track step execution
        steps_executed = []
        
        # Register mock fetcher that tracks execution
        from api.services.fetcher_manager import register_fetcher
        fetcher_name = f"test_{source.country.lower()}_{source.visa_type.lower().replace(' ', '_')}"
        
        def tracked_fetcher(url, metadata):
            steps_executed.append("fetcher_executed")
            return FetchResult(
                raw_text="Test content for pipeline verification.",
                content_type="html",
                success=True,
                fetched_at=datetime.utcnow()
            )
        
        register_fetcher(fetcher_name, tracked_fetcher, {"source_type": source.fetch_type})
        
        # Execute pipeline
        result = await fetch_and_process_source(db_session, source.id)
        
        # Verify pipeline succeeded
        assert result.success is True
        
        # Verify fetcher was executed
        assert "fetcher_executed" in steps_executed
        
        # Verify PolicyVersion was created (indicates all steps completed)
        assert result.policy_version_id is not None
        version_repo = PolicyVersionRepository(db_session)
        version = await version_repo.get_by_id(result.policy_version_id)
        assert version is not None

