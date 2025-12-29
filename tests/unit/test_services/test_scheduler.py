"""Unit tests for scheduler service."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from api.services.scheduler import run_daily_fetch_job, JobResult
from api.services.fetcher_manager import PipelineResult
from api.services.alert_engine import AlertResult
from api.models.db.source import Source


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_source_daily():
    """Sample Source instance with daily check_frequency."""
    source = Mock(spec=Source)
    source.id = uuid.uuid4()
    source.name = "Germany Student Visa"
    source.country = "DE"
    source.visa_type = "Student"
    source.check_frequency = "daily"
    source.is_active = True
    return source


@pytest.fixture
def sample_source_weekly():
    """Sample Source instance with weekly check_frequency."""
    source = Mock(spec=Source)
    source.id = uuid.uuid4()
    source.name = "Germany Work Visa"
    source.country = "DE"
    source.visa_type = "Work"
    source.check_frequency = "weekly"
    source.is_active = True
    return source


@pytest.mark.asyncio
class TestScheduler:
    """Tests for scheduler service."""
    
    @patch('api.services.scheduler.SourceRepository')
    @patch('api.services.scheduler.fetch_and_process_source')
    @patch('api.services.scheduler.AlertEngine')
    async def test_run_daily_fetch_job_success_no_changes(
        self, mock_alert_engine_class, mock_fetch, mock_source_repo_class, mock_db_session,
        sample_source_daily
    ):
        """Test successful job execution with no changes detected."""
        # Setup mocks
        mock_source_repo = Mock()
        mock_source_repo.list_active = AsyncMock(return_value=[sample_source_daily])
        mock_source_repo_class.return_value = mock_source_repo
        
        # Mock pipeline result - no change detected
        pipeline_result = PipelineResult(
            success=True,
            source_id=sample_source_daily.id,
            change_detected=False,
            policy_version_id=uuid.uuid4(),
            policy_change_id=None,
            error_message=None,
            fetched_at=datetime.utcnow()
        )
        mock_fetch.return_value = pipeline_result
        
        # Execute
        result = await run_daily_fetch_job(mock_db_session)
        
        # Verify
        assert isinstance(result, JobResult)
        assert result.sources_processed == 1
        assert result.sources_succeeded == 1
        assert result.sources_failed == 0
        assert result.changes_detected == 0
        assert result.alerts_sent == 0
        assert len(result.errors) == 0
        assert result.completed_at is not None
        
        # Verify fetch was called
        mock_fetch.assert_called_once_with(
            session=mock_db_session,
            source_id=sample_source_daily.id
        )
        
        # Verify alert engine was NOT called (no change detected)
        mock_alert_engine_class.assert_not_called()
    
    @patch('api.services.scheduler.SourceRepository')
    @patch('api.services.scheduler.fetch_and_process_source')
    @patch('api.services.scheduler.AlertEngine')
    async def test_run_daily_fetch_job_success_with_changes(
        self, mock_alert_engine_class, mock_fetch, mock_source_repo_class, mock_db_session,
        sample_source_daily
    ):
        """Test successful job execution with changes detected and alerts sent."""
        # Setup mocks
        mock_source_repo = Mock()
        mock_source_repo.list_active = AsyncMock(return_value=[sample_source_daily])
        mock_source_repo_class.return_value = mock_source_repo
        
        policy_change_id = uuid.uuid4()
        
        # Mock pipeline result - change detected
        pipeline_result = PipelineResult(
            success=True,
            source_id=sample_source_daily.id,
            change_detected=True,
            policy_version_id=uuid.uuid4(),
            policy_change_id=policy_change_id,
            error_message=None,
            fetched_at=datetime.utcnow()
        )
        mock_fetch.return_value = pipeline_result
        
        # Mock alert engine
        mock_alert_engine = Mock()
        alert_result = AlertResult(
            policy_change_id=policy_change_id,
            routes_notified=2,
            emails_sent=2,
            emails_failed=0,
            errors=[]
        )
        mock_alert_engine.send_alerts_for_change = AsyncMock(return_value=alert_result)
        mock_alert_engine_class.return_value = mock_alert_engine
        
        # Execute
        result = await run_daily_fetch_job(mock_db_session)
        
        # Verify
        assert isinstance(result, JobResult)
        assert result.sources_processed == 1
        assert result.sources_succeeded == 1
        assert result.sources_failed == 0
        assert result.changes_detected == 1
        assert result.alerts_sent == 2
        assert len(result.errors) == 0
        
        # Verify alert engine was called
        mock_alert_engine.send_alerts_for_change.assert_called_once_with(
            policy_change_id=policy_change_id
        )
    
    @patch('api.services.scheduler.SourceRepository')
    @patch('api.services.scheduler.fetch_and_process_source')
    @patch('api.services.scheduler.AlertEngine')
    async def test_run_daily_fetch_job_filters_by_check_frequency(
        self, mock_alert_engine_class, mock_fetch, mock_source_repo_class, mock_db_session,
        sample_source_daily, sample_source_weekly
    ):
        """Test that job filters sources by check_frequency (only daily)."""
        # Setup mocks
        mock_source_repo = Mock()
        # Return both daily and weekly sources
        mock_source_repo.list_active = AsyncMock(
            return_value=[sample_source_daily, sample_source_weekly]
        )
        mock_source_repo_class.return_value = mock_source_repo
        
        # Mock pipeline result
        pipeline_result = PipelineResult(
            success=True,
            source_id=sample_source_daily.id,
            change_detected=False,
            policy_version_id=uuid.uuid4(),
            policy_change_id=None,
            error_message=None,
            fetched_at=datetime.utcnow()
        )
        mock_fetch.return_value = pipeline_result
        
        # Execute
        result = await run_daily_fetch_job(mock_db_session)
        
        # Verify - only daily source should be processed
        assert result.sources_processed == 1
        assert result.sources_succeeded == 1
        
        # Verify fetch was called only once (for daily source)
        assert mock_fetch.call_count == 1
        mock_fetch.assert_called_with(
            session=mock_db_session,
            source_id=sample_source_daily.id
        )
    
    @patch('api.services.scheduler.SourceRepository')
    @patch('api.services.scheduler.fetch_and_process_source')
    @patch('api.services.scheduler.AlertEngine')
    async def test_run_daily_fetch_job_handles_source_failure(
        self, mock_alert_engine_class, mock_fetch, mock_source_repo_class, mock_db_session,
        sample_source_daily
    ):
        """Test that job handles source failure gracefully and continues."""
        # Setup mocks
        mock_source_repo = Mock()
        mock_source_repo.list_active = AsyncMock(return_value=[sample_source_daily])
        mock_source_repo_class.return_value = mock_source_repo
        
        # Mock pipeline result - failure
        pipeline_result = PipelineResult(
            success=False,
            source_id=sample_source_daily.id,
            change_detected=False,
            policy_version_id=None,
            policy_change_id=None,
            error_message="Fetch failed",
            fetched_at=datetime.utcnow()
        )
        mock_fetch.return_value = pipeline_result
        
        # Execute
        result = await run_daily_fetch_job(mock_db_session)
        
        # Verify
        assert result.sources_processed == 1
        assert result.sources_succeeded == 0
        assert result.sources_failed == 1
        assert len(result.errors) == 1
        assert "Fetch failed" in result.errors[0]
        
        # Verify alert engine was NOT called
        mock_alert_engine_class.assert_not_called()
    
    @patch('api.services.scheduler.SourceRepository')
    @patch('api.services.scheduler.fetch_and_process_source')
    @patch('api.services.scheduler.AlertEngine')
    async def test_run_daily_fetch_job_handles_exception_gracefully(
        self, mock_alert_engine_class, mock_fetch, mock_source_repo_class, mock_db_session,
        sample_source_daily
    ):
        """Test that job handles exceptions gracefully and continues."""
        # Setup mocks
        mock_source_repo = Mock()
        mock_source_repo.list_active = AsyncMock(return_value=[sample_source_daily])
        mock_source_repo_class.return_value = mock_source_repo
        
        # Mock fetch to raise exception
        mock_fetch.side_effect = Exception("Unexpected error")
        
        # Execute
        result = await run_daily_fetch_job(mock_db_session)
        
        # Verify
        assert result.sources_processed == 1
        assert result.sources_succeeded == 0
        assert result.sources_failed == 1
        assert len(result.errors) == 1
        assert "Unexpected error" in result.errors[0]
    
    @patch('api.services.scheduler.SourceRepository')
    @patch('api.services.scheduler.fetch_and_process_source')
    @patch('api.services.scheduler.AlertEngine')
    async def test_run_daily_fetch_job_handles_alert_failure_gracefully(
        self, mock_alert_engine_class, mock_fetch, mock_source_repo_class, mock_db_session,
        sample_source_daily
    ):
        """Test that alert engine failure doesn't fail the source processing."""
        # Setup mocks
        mock_source_repo = Mock()
        mock_source_repo.list_active = AsyncMock(return_value=[sample_source_daily])
        mock_source_repo_class.return_value = mock_source_repo
        
        policy_change_id = uuid.uuid4()
        
        # Mock pipeline result - change detected
        pipeline_result = PipelineResult(
            success=True,
            source_id=sample_source_daily.id,
            change_detected=True,
            policy_version_id=uuid.uuid4(),
            policy_change_id=policy_change_id,
            error_message=None,
            fetched_at=datetime.utcnow()
        )
        mock_fetch.return_value = pipeline_result
        
        # Mock alert engine to raise exception
        mock_alert_engine = Mock()
        mock_alert_engine.send_alerts_for_change = AsyncMock(
            side_effect=Exception("Alert engine failed")
        )
        mock_alert_engine_class.return_value = mock_alert_engine
        
        # Execute
        result = await run_daily_fetch_job(mock_db_session)
        
        # Verify - source should still be marked as succeeded
        assert result.sources_processed == 1
        assert result.sources_succeeded == 1
        assert result.changes_detected == 1
        assert result.alerts_sent == 0  # No alerts sent due to failure
        assert len(result.errors) == 1
        assert "Alert engine failed" in result.errors[0] or "Failed to send alerts" in result.errors[0]
    
    @patch('api.services.scheduler.SourceRepository')
    @patch('api.services.scheduler.fetch_and_process_source')
    @patch('api.services.scheduler.AlertEngine')
    async def test_run_daily_fetch_job_multiple_sources(
        self, mock_alert_engine_class, mock_fetch, mock_source_repo_class, mock_db_session,
        sample_source_daily
    ):
        """Test job with multiple sources."""
        # Create second daily source
        source2 = Mock(spec=Source)
        source2.id = uuid.uuid4()
        source2.name = "France Student Visa"
        source2.country = "FR"
        source2.visa_type = "Student"
        source2.check_frequency = "daily"
        source2.is_active = True
        
        # Setup mocks
        mock_source_repo = Mock()
        mock_source_repo.list_active = AsyncMock(return_value=[sample_source_daily, source2])
        mock_source_repo_class.return_value = mock_source_repo
        
        # Mock pipeline results
        def pipeline_result_side_effect(session, source_id):
            return PipelineResult(
                success=True,
                source_id=source_id,
                change_detected=False,
                policy_version_id=uuid.uuid4(),
                policy_change_id=None,
                error_message=None,
                fetched_at=datetime.utcnow()
            )
        
        mock_fetch.side_effect = pipeline_result_side_effect
        
        # Execute
        result = await run_daily_fetch_job(mock_db_session)
        
        # Verify
        assert result.sources_processed == 2
        assert result.sources_succeeded == 2
        assert result.sources_failed == 0
        assert mock_fetch.call_count == 2
    
    @patch('api.services.scheduler.SourceRepository')
    async def test_run_daily_fetch_job_no_sources(
        self, mock_source_repo_class, mock_db_session
    ):
        """Test job with no active sources."""
        # Setup mocks
        mock_source_repo = Mock()
        mock_source_repo.list_active = AsyncMock(return_value=[])
        mock_source_repo_class.return_value = mock_source_repo
        
        # Execute
        result = await run_daily_fetch_job(mock_db_session)
        
        # Verify
        assert result.sources_processed == 0
        assert result.sources_succeeded == 0
        assert result.sources_failed == 0
        assert result.completed_at is not None
    
    @patch('api.services.scheduler.SourceRepository')
    async def test_run_daily_fetch_job_no_daily_sources(
        self, mock_source_repo_class, mock_db_session, sample_source_weekly
    ):
        """Test job with no daily sources (only weekly)."""
        # Setup mocks
        mock_source_repo = Mock()
        mock_source_repo.list_active = AsyncMock(return_value=[sample_source_weekly])
        mock_source_repo_class.return_value = mock_source_repo
        
        # Execute
        result = await run_daily_fetch_job(mock_db_session)
        
        # Verify
        assert result.sources_processed == 0
        assert result.sources_succeeded == 0
        assert result.sources_failed == 0

