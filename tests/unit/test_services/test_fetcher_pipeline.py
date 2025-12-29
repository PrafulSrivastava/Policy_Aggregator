"""Unit tests for fetch and process pipeline."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from api.services.fetcher_manager import fetch_and_process_source, PipelineResult, _retry_with_backoff
from api.repositories.source_repository import SourceRepository
from fetchers.base import FetchResult


@pytest.mark.asyncio
class TestFetchAndProcessSource:
    """Tests for fetch_and_process_source() function."""
    
    async def test_source_not_found(self, db_session):
        """Test pipeline fails when source not found."""
        source_id = uuid.uuid4()
        
        result = await fetch_and_process_source(db_session, source_id)
        
        assert result.success is False
        assert result.source_id == source_id
        assert "not found" in result.error_message.lower()
        assert result.policy_version_id is None
    
    async def test_source_not_active(self, db_session, sample_source_data):
        """Test pipeline fails when source is not active."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create({**sample_source_data, "is_active": False})
        
        result = await fetch_and_process_source(db_session, source.id)
        
        assert result.success is False
        assert result.source_id == source.id
        assert "not active" in result.error_message.lower()
    
    async def test_no_fetcher_found(self, db_session, sample_source_data):
        """Test pipeline fails when no fetcher found for source."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Mock get_fetcher_for_source to return None
        with patch('api.services.fetcher_manager.get_fetcher_for_source', return_value=None):
            result = await fetch_and_process_source(db_session, source.id)
        
        assert result.success is False
        assert result.source_id == source.id
        assert "no fetcher found" in result.error_message.lower()
    
    async def test_fetcher_execution_failure(self, db_session, sample_source_data):
        """Test pipeline handles fetcher execution failure."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Mock fetcher that raises exception
        def failing_fetcher(url, metadata):
            raise Exception("Network error")
        
        with patch('api.services.fetcher_manager.get_fetcher_for_source', return_value=failing_fetcher):
            result = await fetch_and_process_source(db_session, source.id)
        
        assert result.success is False
        assert result.source_id == source.id
        assert "fetcher execution failed" in result.error_message.lower()
    
    async def test_fetcher_returns_error(self, db_session, sample_source_data):
        """Test pipeline handles fetcher returning error result."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Mock fetcher that returns error
        def error_fetcher(url, metadata):
            return FetchResult(
                raw_text="",
                content_type="html",
                success=False,
                error_message="Connection timeout"
            )
        
        with patch('api.services.fetcher_manager.get_fetcher_for_source', return_value=error_fetcher):
            result = await fetch_and_process_source(db_session, source.id)
        
        assert result.success is False
        assert result.source_id == source.id
        assert "fetcher returned error" in result.error_message.lower()
    
    async def test_empty_fetcher_content(self, db_session, sample_source_data):
        """Test pipeline handles empty fetcher content."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Mock fetcher that returns empty content
        def empty_fetcher(url, metadata):
            return FetchResult(
                raw_text="",
                content_type="html",
                success=True
            )
        
        with patch('api.services.fetcher_manager.get_fetcher_for_source', return_value=empty_fetcher):
            result = await fetch_and_process_source(db_session, source.id)
        
        assert result.success is False
        assert result.source_id == source.id
        assert "empty content" in result.error_message.lower()
    
    async def test_normalization_failure(self, db_session, sample_source_data):
        """Test pipeline handles normalization failure."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Mock fetcher that returns content
        def success_fetcher(url, metadata):
            return FetchResult(
                raw_text="Test content",
                content_type="html",
                success=True
            )
        
        # Mock normalize to raise exception
        with patch('api.services.fetcher_manager.get_fetcher_for_source', return_value=success_fetcher), \
             patch('api.services.fetcher_manager.normalize', side_effect=Exception("Normalization error")):
            result = await fetch_and_process_source(db_session, source.id)
        
        assert result.success is False
        assert result.source_id == source.id
        assert "normalization failed" in result.error_message.lower()
    
    async def test_version_storage_failure(self, db_session, sample_source_data):
        """Test pipeline handles version storage failure."""
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Mock fetcher
        def success_fetcher(url, metadata):
            return FetchResult(
                raw_text="Test content",
                content_type="html",
                success=True,
                fetched_at=datetime.utcnow()
            )
        
        # Mock store_policy_version to raise exception
        with patch('api.services.fetcher_manager.get_fetcher_for_source', return_value=success_fetcher), \
             patch('api.services.fetcher_manager.store_policy_version', side_effect=Exception("Storage error")):
            result = await fetch_and_process_source(db_session, source.id)
        
        assert result.success is False
        assert result.source_id == source.id
        assert "version storage failed" in result.error_message.lower()


class TestRetryLogic:
    """Tests for retry logic."""
    
    def test_retry_succeeds_on_second_attempt(self):
        """Test retry succeeds after initial failure."""
        attempt_count = [0]
        
        def flaky_function():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ConnectionError("Temporary connection error")
            return "success"
        
        result = _retry_with_backoff(
            flaky_function,
            max_retries=3,
            initial_delay=0.1,
            backoff_factor=1.0
        )
        
        assert result == "success"
        assert attempt_count[0] == 2
    
    def test_retry_exhausts_all_attempts(self):
        """Test retry exhausts all attempts before failing."""
        attempt_count = [0]
        
        def always_failing_function():
            attempt_count[0] += 1
            raise ConnectionError("Persistent connection error")
        
        with pytest.raises(ConnectionError):
            _retry_with_backoff(
                always_failing_function,
                max_retries=3,
                initial_delay=0.1,
                backoff_factor=1.0
            )
        
        assert attempt_count[0] == 3
    
    def test_retry_does_not_retry_permanent_failures(self):
        """Test retry does not retry permanent failures (404)."""
        attempt_count = [0]
        
        class NotFoundError(Exception):
            status_code = 404
        
        def permanent_failure():
            attempt_count[0] += 1
            raise NotFoundError("Not found")
        
        with pytest.raises(NotFoundError):
            _retry_with_backoff(
                permanent_failure,
                max_retries=3,
                initial_delay=0.1
            )
        
        # Should only attempt once (no retries for permanent failures)
        assert attempt_count[0] == 1
    
    def test_retry_handles_timeout_errors(self):
        """Test retry handles timeout errors."""
        attempt_count = [0]
        
        def timeout_function():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise TimeoutError("Request timeout")
            return "success"
        
        result = _retry_with_backoff(
            timeout_function,
            max_retries=3,
            initial_delay=0.1
        )
        
        assert result == "success"
        assert attempt_count[0] == 2

