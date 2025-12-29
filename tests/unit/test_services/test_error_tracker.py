"""Unit tests for error tracker service."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from api.services.error_tracker import ErrorTracker, FAILURE_THRESHOLD
from api.models.db.source import Source


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_source():
    """Sample Source instance."""
    source = Mock(spec=Source)
    source.id = uuid.uuid4()
    source.name = "Germany Student Visa"
    source.url = "https://example.com/germany-student-visa"
    source.country = "DE"
    source.visa_type = "Student"
    source.consecutive_fetch_failures = 0
    source.consecutive_email_failures = 0
    source.last_fetch_error = None
    source.last_email_error = None
    source.last_checked_at = datetime.utcnow()
    return source


@pytest.mark.asyncio
class TestErrorTracker:
    """Tests for ErrorTracker service."""
    
    @patch('api.services.error_tracker.SourceRepository')
    async def test_record_fetch_success_resets_count(
        self, mock_source_repo_class, mock_db_session, sample_source
    ):
        """Test that recording fetch success resets failure count."""
        # Setup
        sample_source.consecutive_fetch_failures = 3
        sample_source.last_fetch_error = "Previous error"
        
        mock_source_repo = Mock()
        mock_source_repo.get_by_id = AsyncMock(return_value=sample_source)
        mock_source_repo.update = AsyncMock()
        mock_source_repo_class.return_value = mock_source_repo
        
        error_tracker = ErrorTracker(mock_db_session)
        
        # Execute
        await error_tracker.record_fetch_success(sample_source.id)
        
        # Verify
        mock_source_repo.update.assert_called_once()
        call_args = mock_source_repo.update.call_args
        assert call_args[0][0] == sample_source.id
        assert call_args[0][1]["consecutive_fetch_failures"] == 0
        assert call_args[0][1]["last_fetch_error"] is None
    
    @patch('api.services.error_tracker.SourceRepository')
    async def test_record_fetch_failure_increments_count(
        self, mock_source_repo_class, mock_db_session, sample_source
    ):
        """Test that recording fetch failure increments count."""
        # Setup
        sample_source.consecutive_fetch_failures = 1
        
        mock_source_repo = Mock()
        mock_source_repo.get_by_id = AsyncMock(return_value=sample_source)
        mock_source_repo.update = AsyncMock()
        mock_source_repo_class.return_value = mock_source_repo
        
        error_tracker = ErrorTracker(mock_db_session)
        error_tracker._send_admin_notification = AsyncMock()
        
        # Execute
        await error_tracker.record_fetch_failure(
            source_id=sample_source.id,
            error_message="Test error"
        )
        
        # Verify
        mock_source_repo.update.assert_called_once()
        call_args = mock_source_repo.update.call_args
        assert call_args[0][0] == sample_source.id
        assert call_args[0][1]["consecutive_fetch_failures"] == 2
        assert call_args[0][1]["last_fetch_error"] == "Test error"
    
    @patch('api.services.error_tracker.SourceRepository')
    async def test_record_fetch_failure_sends_notification_at_threshold(
        self, mock_source_repo_class, mock_db_session, sample_source
    ):
        """Test that notification is sent when threshold is exceeded."""
        # Setup - source has 2 failures, will become 3 (threshold)
        sample_source.consecutive_fetch_failures = FAILURE_THRESHOLD - 1
        
        # Create updated source for threshold check
        updated_source = Mock()
        updated_source.id = sample_source.id
        updated_source.name = sample_source.name
        updated_source.consecutive_fetch_failures = FAILURE_THRESHOLD
        updated_source.consecutive_email_failures = sample_source.consecutive_email_failures
        
        mock_source_repo = Mock()
        # First call returns original source, second call (for threshold check) returns updated source
        mock_source_repo.get_by_id = AsyncMock(side_effect=[sample_source, updated_source])
        mock_source_repo.update = AsyncMock()
        mock_source_repo_class.return_value = mock_source_repo
        
        error_tracker = ErrorTracker(mock_db_session)
        error_tracker._send_admin_notification = AsyncMock()
        
        # Execute
        await error_tracker.record_fetch_failure(
            source_id=sample_source.id,
            error_message="Test error"
        )
        
        # Verify notification was called
        error_tracker._send_admin_notification.assert_called_once()
        call_args = error_tracker._send_admin_notification.call_args
        # The source passed is the original source (before update), but failure_count is updated
        assert call_args[1]["source"].id == sample_source.id
        assert call_args[1]["error_type"] == "fetch"
        assert call_args[1]["failure_count"] == FAILURE_THRESHOLD
        assert call_args[1]["error_message"] == "Test error"
    
    @patch('api.services.error_tracker.SourceRepository')
    async def test_record_fetch_failure_no_notification_below_threshold(
        self, mock_source_repo_class, mock_db_session, sample_source
    ):
        """Test that notification is not sent when below threshold."""
        # Setup - source has 0 failures, will become 1 (below threshold)
        sample_source.consecutive_fetch_failures = 0
        
        mock_source_repo = Mock()
        mock_source_repo.get_by_id = AsyncMock(return_value=sample_source)
        mock_source_repo.update = AsyncMock()
        mock_source_repo_class.return_value = mock_source_repo
        
        error_tracker = ErrorTracker(mock_db_session)
        error_tracker._send_admin_notification = AsyncMock()
        
        # Execute
        await error_tracker.record_fetch_failure(
            source_id=sample_source.id,
            error_message="Test error"
        )
        
        # Verify notification was NOT called
        error_tracker._send_admin_notification.assert_not_called()
    
    @patch('api.services.error_tracker.SourceRepository')
    async def test_record_email_failure_tracks_separately(
        self, mock_source_repo_class, mock_db_session, sample_source
    ):
        """Test that email failures are tracked separately from fetch failures."""
        # Setup
        sample_source.consecutive_fetch_failures = 2
        sample_source.consecutive_email_failures = 1
        
        mock_source_repo = Mock()
        mock_source_repo.get_by_id = AsyncMock(return_value=sample_source)
        mock_source_repo.update = AsyncMock()
        mock_source_repo_class.return_value = mock_source_repo
        
        error_tracker = ErrorTracker(mock_db_session)
        error_tracker._send_admin_notification = AsyncMock()
        
        # Execute
        await error_tracker.record_email_failure(
            source_id=sample_source.id,
            error_message="Email error"
        )
        
        # Verify
        call_args = mock_source_repo.update.call_args
        # Fetch failures should remain unchanged
        assert "consecutive_fetch_failures" not in call_args[0][1]
        # Email failures should be incremented
        assert call_args[0][1]["consecutive_email_failures"] == 2
        assert call_args[0][1]["last_email_error"] == "Email error"
    
    @patch('api.services.error_tracker.SourceRepository')
    async def test_check_failure_threshold_fetch(
        self, mock_source_repo_class, mock_db_session, sample_source
    ):
        """Test threshold checking for fetch errors."""
        mock_source_repo = Mock()
        mock_source_repo.get_by_id = AsyncMock(return_value=sample_source)
        mock_source_repo_class.return_value = mock_source_repo
        
        error_tracker = ErrorTracker(mock_db_session)
        
        # Test below threshold
        sample_source.consecutive_fetch_failures = FAILURE_THRESHOLD - 1
        result = await error_tracker.check_failure_threshold(sample_source.id, "fetch")
        assert result is False
        
        # Test at threshold
        sample_source.consecutive_fetch_failures = FAILURE_THRESHOLD
        result = await error_tracker.check_failure_threshold(sample_source.id, "fetch")
        assert result is True
        
        # Test above threshold
        sample_source.consecutive_fetch_failures = FAILURE_THRESHOLD + 1
        result = await error_tracker.check_failure_threshold(sample_source.id, "fetch")
        assert result is True
    
    @patch('api.services.error_tracker.SourceRepository')
    async def test_check_failure_threshold_email(
        self, mock_source_repo_class, mock_db_session, sample_source
    ):
        """Test threshold checking for email errors."""
        mock_source_repo = Mock()
        mock_source_repo.get_by_id = AsyncMock(return_value=sample_source)
        mock_source_repo_class.return_value = mock_source_repo
        
        error_tracker = ErrorTracker(mock_db_session)
        
        # Test below threshold
        sample_source.consecutive_email_failures = FAILURE_THRESHOLD - 1
        result = await error_tracker.check_failure_threshold(sample_source.id, "email")
        assert result is False
        
        # Test at threshold
        sample_source.consecutive_email_failures = FAILURE_THRESHOLD
        result = await error_tracker.check_failure_threshold(sample_source.id, "email")
        assert result is True
    
    @patch('api.services.error_tracker.get_email_service')
    @patch('api.services.error_tracker.SourceRepository')
    @patch('api.services.error_tracker.settings')
    async def test_send_admin_notification(
        self, mock_settings, mock_source_repo_class, mock_get_email,
        mock_db_session, sample_source
    ):
        """Test admin notification sending."""
        # Setup
        mock_settings.ADMIN_EMAIL = "admin@example.com"
        
        mock_email_service = Mock()
        mock_email_service.send_email = Mock(return_value=Mock(success=True, message_id="email_123"))
        mock_get_email.return_value = mock_email_service
        
        error_tracker = ErrorTracker(mock_db_session)
        error_tracker.email_service = mock_email_service
        
        # Execute
        await error_tracker._send_admin_notification(
            source=sample_source,
            error_type="fetch",
            failure_count=3,
            error_message="Test error"
        )
        
        # Verify email was sent
        mock_email_service.send_email.assert_called_once()
        call_args = mock_email_service.send_email.call_args
        assert call_args[1]["recipient"] == "admin@example.com"
        assert "Policy Aggregator" in call_args[1]["subject"]
        assert "Test error" in call_args[1]["html_body"]
        assert "Test error" in call_args[1]["text_body"]
    
    @patch('api.services.error_tracker.SourceRepository')
    async def test_record_fetch_success_source_not_found(
        self, mock_source_repo_class, mock_db_session
    ):
        """Test handling when source is not found."""
        mock_source_repo = Mock()
        mock_source_repo.get_by_id = AsyncMock(return_value=None)
        mock_source_repo_class.return_value = mock_source_repo
        
        error_tracker = ErrorTracker(mock_db_session)
        
        # Execute - should not raise exception
        await error_tracker.record_fetch_success(uuid.uuid4())
        
        # Verify update was not called
        mock_source_repo.update.assert_not_called()

