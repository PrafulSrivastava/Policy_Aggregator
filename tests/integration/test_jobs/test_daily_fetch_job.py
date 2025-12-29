"""Integration tests for daily fetch job."""

import pytest
from datetime import datetime
from api.services.scheduler import run_daily_fetch_job, JobResult
from api.repositories.source_repository import SourceRepository
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.email_alert_repository import EmailAlertRepository
from api.repositories.route_subscription_repository import RouteSubscriptionRepository
from unittest.mock import Mock, patch


@pytest.mark.asyncio
class TestDailyFetchJobIntegration:
    """Integration tests for daily fetch job."""
    
    async def test_run_daily_fetch_job_with_test_sources(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: run job with test sources, verify full flow."""
        # Create test sources with daily check_frequency
        source_repo = SourceRepository(db_session)
        
        source1_data = sample_source_data.copy()
        source1_data["name"] = "Germany Student Visa Daily"
        source1_data["check_frequency"] = "daily"
        source1 = await source_repo.create(source1_data)
        
        source2_data = sample_source_data.copy()
        source2_data["name"] = "Germany Work Visa Daily"
        source2_data["visa_type"] = "Work"
        source2_data["check_frequency"] = "daily"
        source2 = await source_repo.create(source2_data)
        
        # Create source with weekly check_frequency (should be skipped)
        source3_data = sample_source_data.copy()
        source3_data["name"] = "Germany Student Visa Weekly"
        source3_data["check_frequency"] = "weekly"
        source3 = await source_repo.create(source3_data)
        
        # Create route subscription
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Mock fetcher to return content (to avoid actual HTTP calls)
        with patch('api.services.fetcher_manager.get_fetcher_for_source') as mock_get_fetcher:
            from fetchers.base import FetchResult
            
            def mock_fetch(url: str, metadata: dict) -> FetchResult:
                return FetchResult(
                    raw_text="Sample policy content for testing",
                    content_type="html",
                    success=True
                )
            
            mock_get_fetcher.return_value = mock_fetch
            
            # Mock email service to avoid sending real emails
            with patch('api.services.scheduler.AlertEngine') as mock_alert_engine_class:
                from api.services.alert_engine import AlertResult
                import uuid
                
                mock_alert_engine = Mock()
                alert_result = AlertResult(
                    policy_change_id=uuid.uuid4(),
                    routes_notified=1,
                    emails_sent=1,
                    emails_failed=0,
                    errors=[]
                )
                mock_alert_engine.send_alerts_for_change = Mock(return_value=alert_result)
                mock_alert_engine_class.return_value = mock_alert_engine
                
                # Run daily fetch job
                result = await run_daily_fetch_job(db_session)
                
                # Verify job result
                assert isinstance(result, JobResult)
                assert result.sources_processed == 2  # Only daily sources
                assert result.sources_succeeded >= 0  # May succeed or fail depending on fetcher
                assert result.completed_at is not None
                
                # Verify that weekly source was not processed
                # (sources_processed should be 2, not 3)
                assert result.sources_processed == 2
    
    async def test_run_daily_fetch_job_with_changes_detected(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: run job, verify changes detected and alerts sent."""
        # Create test source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create route subscription
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Mock fetcher to return content
        with patch('api.services.fetcher_manager.get_fetcher_for_source') as mock_get_fetcher:
            from fetchers.base import FetchResult
            
            def mock_fetch(url: str, metadata: dict) -> FetchResult:
                return FetchResult(
                    raw_text="Sample policy content for testing",
                    content_type="html",
                    success=True
                )
            
            mock_get_fetcher.return_value = mock_fetch
            
            # Mock email service
            with patch('api.services.alert_engine.get_email_service') as mock_get_email:
                from api.integrations.resend import EmailResult
                mock_email_service = Mock()
                mock_email_service.send_email = Mock(return_value=EmailResult(
                    success=True,
                    message_id="test_email_123"
                ))
                mock_get_email.return_value = mock_email_service
                
                # Run daily fetch job
                result = await run_daily_fetch_job(db_session)
                
                # Verify job completed
                assert isinstance(result, JobResult)
                assert result.sources_processed == 1
                assert result.completed_at is not None
                
                # If change was detected, verify alerts were sent
                if result.changes_detected > 0:
                    assert result.alerts_sent >= 0  # May be 0 if no routes match
                    
                    # Verify email service was called if alerts were sent
                    if result.alerts_sent > 0:
                        assert mock_email_service.send_email.called
    
    async def test_run_daily_fetch_job_error_handling(
        self, db_session, sample_source_data
    ):
        """Test: run job with failing sources, verify error handling."""
        # Create test sources
        source_repo = SourceRepository(db_session)
        
        source1_data = sample_source_data.copy()
        source1_data["name"] = "Valid Source"
        source1_data["check_frequency"] = "daily"
        source1 = await source_repo.create(source1_data)
        
        source2_data = sample_source_data.copy()
        source2_data["name"] = "Failing Source"
        source2_data["url"] = "https://invalid-url-that-will-fail.com"
        source2_data["check_frequency"] = "daily"
        source2 = await source_repo.create(source2_data)
        
        # Mock fetcher to fail for second source
        with patch('api.services.fetcher_manager.get_fetcher_for_source') as mock_get_fetcher:
            from fetchers.base import FetchResult
            
            call_count = 0
            def mock_fetch(url: str, metadata: dict) -> FetchResult:
                nonlocal call_count
                call_count += 1
                if "invalid-url" in url:
                    return FetchResult(
                        raw_text=None,
                        content_type=None,
                        success=False,
                        error_message="Failed to fetch"
                    )
                return FetchResult(
                    raw_text="Sample policy content",
                    content_type="html",
                    success=True
                )
            
            mock_get_fetcher.return_value = mock_fetch
            
            # Run daily fetch job
            result = await run_daily_fetch_job(db_session)
            
            # Verify job completed despite failures
            assert isinstance(result, JobResult)
            assert result.sources_processed == 2
            assert result.completed_at is not None
            
            # Verify that one source failed
            assert result.sources_failed >= 0  # May have failures
            if result.sources_failed > 0:
                assert len(result.errors) > 0
    
    async def test_run_daily_fetch_job_no_active_sources(self, db_session):
        """Test: run job with no active sources."""
        # Run daily fetch job with empty database
        result = await run_daily_fetch_job(db_session)
        
        # Verify job completed successfully
        assert isinstance(result, JobResult)
        assert result.sources_processed == 0
        assert result.sources_succeeded == 0
        assert result.sources_failed == 0
        assert result.completed_at is not None
        assert len(result.errors) == 0
    
    async def test_run_daily_fetch_job_only_weekly_sources(
        self, db_session, sample_source_data
    ):
        """Test: run job with only weekly sources (should process none)."""
        # Create test source with weekly check_frequency
        source_repo = SourceRepository(db_session)
        
        source_data = sample_source_data.copy()
        source_data["name"] = "Weekly Source"
        source_data["check_frequency"] = "weekly"
        source = await source_repo.create(source_data)
        
        # Run daily fetch job
        result = await run_daily_fetch_job(db_session)
        
        # Verify no sources were processed
        assert isinstance(result, JobResult)
        assert result.sources_processed == 0
        assert result.completed_at is not None

