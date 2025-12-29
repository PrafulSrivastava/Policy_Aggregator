"""Integration tests for error notification system."""

import pytest
from datetime import datetime
from api.services.error_tracker import ErrorTracker, FAILURE_THRESHOLD
from api.repositories.source_repository import SourceRepository
from unittest.mock import Mock, patch


@pytest.mark.asyncio
class TestErrorNotificationIntegration:
    """Integration tests for error notification system."""
    
    async def test_simulate_failures_verify_notification_sent(
        self, db_session, sample_source_data
    ):
        """Test: simulate failures, verify notification sent."""
        # Create test source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Mock email service
        with patch('api.services.error_tracker.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=True,
                message_id="test_email_123"
            ))
            mock_get_email.return_value = mock_email_service
            
            # Mock admin email setting
            with patch('api.services.error_tracker.settings') as mock_settings:
                mock_settings.ADMIN_EMAIL = "admin@example.com"
                
                error_tracker = ErrorTracker(db_session)
                error_tracker.email_service = mock_email_service
                
                # Simulate 3 consecutive fetch failures
                for i in range(FAILURE_THRESHOLD):
                    await error_tracker.record_fetch_failure(
                        source_id=source.id,
                        error_message=f"Test error {i+1}"
                    )
                    
                    # Refresh source from database
                    source = await source_repo.get_by_id(source.id)
                
                # Verify failure count is 3
                assert source.consecutive_fetch_failures == FAILURE_THRESHOLD
                assert source.last_fetch_error == f"Test error {FAILURE_THRESHOLD}"
                
                # Verify notification was sent (should be called once when threshold reached)
                assert mock_email_service.send_email.call_count == 1
                
                # Verify notification content
                call_args = mock_email_service.send_email.call_args
                assert call_args[1]["recipient"] == "admin@example.com"
                assert "Policy Aggregator" in call_args[1]["subject"]
                assert source.name in call_args[1]["html_body"]
                assert source.url in call_args[1]["html_body"]
                assert str(FAILURE_THRESHOLD) in call_args[1]["html_body"]
                assert f"Test error {FAILURE_THRESHOLD}" in call_args[1]["html_body"]
    
    async def test_success_resets_failure_count(
        self, db_session, sample_source_data
    ):
        """Test: success resets failure count."""
        # Create test source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        error_tracker = ErrorTracker(db_session)
        
        # Simulate 2 failures
        for i in range(2):
            await error_tracker.record_fetch_failure(
                source_id=source.id,
                error_message=f"Test error {i+1}"
            )
            source = await source_repo.get_by_id(source.id)
        
        # Verify failure count is 2
        assert source.consecutive_fetch_failures == 2
        
        # Record success
        await error_tracker.record_fetch_success(source.id)
        
        # Refresh source from database
        source = await source_repo.get_by_id(source.id)
        
        # Verify failure count is reset
        assert source.consecutive_fetch_failures == 0
        assert source.last_fetch_error is None
    
    async def test_fetch_and_email_failures_tracked_separately(
        self, db_session, sample_source_data
    ):
        """Test that fetch and email failures are tracked separately."""
        # Create test source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        error_tracker = ErrorTracker(db_session)
        
        # Record fetch failures
        await error_tracker.record_fetch_failure(
            source_id=source.id,
            error_message="Fetch error"
        )
        await error_tracker.record_fetch_failure(
            source_id=source.id,
            error_message="Fetch error 2"
        )
        
        # Record email failure
        await error_tracker.record_email_failure(
            source_id=source.id,
            error_message="Email error"
        )
        
        # Refresh source from database
        source = await source_repo.get_by_id(source.id)
        
        # Verify they are tracked separately
        assert source.consecutive_fetch_failures == 2
        assert source.consecutive_email_failures == 1
        assert source.last_fetch_error == "Fetch error 2"
        assert source.last_email_error == "Email error"
    
    async def test_notification_not_sent_below_threshold(
        self, db_session, sample_source_data
    ):
        """Test that notification is not sent when below threshold."""
        # Create test source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Mock email service
        with patch('api.services.error_tracker.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=True,
                message_id="test_email_123"
            ))
            mock_get_email.return_value = mock_email_service
            
            # Mock admin email setting
            with patch('api.services.error_tracker.settings') as mock_settings:
                mock_settings.ADMIN_EMAIL = "admin@example.com"
                
                error_tracker = ErrorTracker(db_session)
                error_tracker.email_service = mock_email_service
                
                # Simulate failures below threshold
                for i in range(FAILURE_THRESHOLD - 1):
                    await error_tracker.record_fetch_failure(
                        source_id=source.id,
                        error_message=f"Test error {i+1}"
                    )
                
                # Verify notification was NOT sent
                mock_email_service.send_email.assert_not_called()
    
    async def test_notification_includes_last_successful_fetch(
        self, db_session, sample_source_data
    ):
        """Test that notification includes last successful fetch timestamp."""
        # Create test source with last_checked_at
        source_repo = SourceRepository(db_session)
        source_data = sample_source_data.copy()
        source_data["last_checked_at"] = datetime.utcnow()
        source = await source_repo.create(source_data)
        
        # Mock email service
        with patch('api.services.error_tracker.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=True,
                message_id="test_email_123"
            ))
            mock_get_email.return_value = mock_email_service
            
            # Mock admin email setting
            with patch('api.services.error_tracker.settings') as mock_settings:
                mock_settings.ADMIN_EMAIL = "admin@example.com"
                
                error_tracker = ErrorTracker(db_session)
                error_tracker.email_service = mock_email_service
                
                # Simulate failures to reach threshold
                for i in range(FAILURE_THRESHOLD):
                    await error_tracker.record_fetch_failure(
                        source_id=source.id,
                        error_message=f"Test error {i+1}"
                    )
                
                # Verify notification includes last successful fetch
                call_args = mock_email_service.send_email.call_args
                assert source.last_checked_at.isoformat() in call_args[1]["html_body"]
                assert source.last_checked_at.isoformat() in call_args[1]["text_body"]

