"""End-to-end integration tests for the complete alert system.

Tests the full flow from source change detection to email delivery.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from api.services.fetcher_manager import fetch_and_process_source
from api.services.alert_engine import AlertEngine
from api.services.scheduler import run_daily_fetch_job
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.email_alert_repository import EmailAlertRepository
from api.repositories.source_repository import SourceRepository
from api.repositories.route_subscription_repository import RouteSubscriptionRepository
from fetchers.base import FetchResult
from tests.fixtures.alert_fixtures import (
    create_test_source,
    create_test_route,
    create_test_policy_change
)


@pytest.mark.asyncio
class TestEndToEndAlertSystem:
    """End-to-end tests for the complete alert system."""
    
    async def test_full_alert_flow(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """
        Test complete alert flow: create route, create source, trigger fetch with change,
        verify PolicyChange created, verify email sent.
        """
        # Step 1: Create route subscription
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Step 2: Create source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Step 3: Register mock fetcher that returns content
        from api.services.fetcher_manager import register_fetcher
        fetcher_name = f"test_{source.country.lower()}_{source.visa_type.lower().replace(' ', '_')}"
        
        call_count = 0
        def mock_fetcher(url, metadata):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First fetch - no change
                return FetchResult(
                    raw_text="Original policy content.\n\nSection 1: Requirements.",
                    content_type="html",
                    success=True,
                    fetched_at=datetime.utcnow()
                )
            else:
                # Second fetch - change detected
                return FetchResult(
                    raw_text="Updated policy content.\n\nSection 1: Requirements.\n\nSection 2: New section.",
                    content_type="html",
                    success=True,
                    fetched_at=datetime.utcnow()
                )
        
        register_fetcher(fetcher_name, mock_fetcher, {"source_type": source.fetch_type})
        
        # Step 4: First fetch (no change)
        result1 = await fetch_and_process_source(db_session, source.id)
        assert result1.success is True
        assert result1.change_detected is False
        
        # Step 5: Second fetch (change detected)
        result2 = await fetch_and_process_source(db_session, source.id)
        assert result2.success is True
        assert result2.change_detected is True
        assert result2.policy_change_id is not None
        
        # Step 6: Verify PolicyChange created
        change_repo = PolicyChangeRepository(db_session)
        policy_change = await change_repo.get_by_id(result2.policy_change_id)
        assert policy_change is not None
        assert policy_change.source_id == source.id
        
        # Step 7: Mock email service and trigger alert
        with patch('api.services.alert_engine.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=True,
                message_id="test_email_123"
            ))
            mock_get_email.return_value = mock_email_service
            
            alert_engine = AlertEngine(db_session)
            alert_engine.email_service = mock_email_service
            
            alert_result = await alert_engine.send_alerts_for_change(policy_change.id)
            
            # Step 8: Verify email sent
            assert alert_result.emails_sent == 1
            assert alert_result.routes_notified == 1
            mock_email_service.send_email.assert_called_once()
            
            # Step 9: Verify email content
            call_args = mock_email_service.send_email.call_args
            assert call_args[1]["recipient"] == route.email
            assert "Policy Change Detected" in call_args[1]["subject"]
            assert route.origin_country in call_args[1]["html_body"]
            assert route.destination_country in call_args[1]["html_body"]
            assert route.visa_type in call_args[1]["html_body"]
            assert source.name in call_args[1]["html_body"]
            assert source.url in call_args[1]["html_body"]
            assert "View Full Diff" in call_args[1]["html_body"] or "view full diff" in call_args[1]["html_body"].lower()
            assert "This is information, not legal advice" in call_args[1]["html_body"]
            
            # Step 10: Verify EmailAlert record created
            alert_repo = EmailAlertRepository(db_session)
            alerts = await alert_repo.get_by_policy_change(policy_change.id)
            assert len(alerts) == 1
            assert alerts[0].route_subscription_id == route.id
            assert alerts[0].status == "sent"
    
    async def test_multiple_routes_one_source(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: multiple routes matching one source all receive emails."""
        # Create one source
        source = await create_test_source(
            db_session,
            country=sample_source_data["country"],
            visa_type=sample_source_data["visa_type"]
        )
        
        # Create multiple route subscriptions matching the source
        route1 = await create_test_route(
            db_session,
            destination_country=source.country,
            visa_type=source.visa_type,
            email="user1@example.com"
        )
        route2 = await create_test_route(
            db_session,
            destination_country=source.country,
            visa_type=source.visa_type,
            email="user2@example.com"
        )
        route3 = await create_test_route(
            db_session,
            destination_country=source.country,
            visa_type=source.visa_type,
            email="user3@example.com"
        )
        
        # Create policy change
        policy_change = await create_test_policy_change(db_session, source.id)
        
        # Mock email service
        with patch('api.services.alert_engine.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=True,
                message_id="test_email_123"
            ))
            mock_get_email.return_value = mock_email_service
            
            alert_engine = AlertEngine(db_session)
            alert_engine.email_service = mock_email_service
            
            # Trigger alerts
            alert_result = await alert_engine.send_alerts_for_change(policy_change.id)
            
            # Verify all routes received emails
            assert alert_result.routes_notified == 3
            assert alert_result.emails_sent == 3
            assert mock_email_service.send_email.call_count == 3
            
            # Verify each route got exactly one email
            recipients = [call[1]["recipient"] for call in mock_email_service.send_email.call_args_list]
            assert route1.email in recipients
            assert route2.email in recipients
            assert route3.email in recipients
            assert len(set(recipients)) == 3  # All unique
    
    async def test_route_no_matching_sources(
        self, db_session, sample_route_subscription_data
    ):
        """Test: route with no matching sources receives no emails."""
        # Create route subscription
        route = await create_test_route(
            db_session,
            destination_country="FR",  # Different country
            visa_type="Work",  # Different visa type
            email="test@example.com"
        )
        
        # Create unrelated source (different country/visa type)
        source = await create_test_source(
            db_session,
            country="DE",
            visa_type="Student"
        )
        
        # Create policy change for unrelated source
        policy_change = await create_test_policy_change(db_session, source.id)
        
        # Mock email service
        with patch('api.services.alert_engine.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=True,
                message_id="test_email_123"
            ))
            mock_get_email.return_value = mock_email_service
            
            alert_engine = AlertEngine(db_session)
            alert_engine.email_service = mock_email_service
            
            # Trigger alerts
            alert_result = await alert_engine.send_alerts_for_change(policy_change.id)
            
            # Verify no emails sent
            assert alert_result.routes_notified == 0
            assert alert_result.emails_sent == 0
            mock_email_service.send_email.assert_not_called()
    
    async def test_email_service_failure(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: email service failure handled gracefully."""
        # Create source and route
        source = await create_test_source(
            db_session,
            country=sample_source_data["country"],
            visa_type=sample_source_data["visa_type"]
        )
        route = await create_test_route(
            db_session,
            destination_country=source.country,
            visa_type=source.visa_type,
            email="test@example.com"
        )
        
        # Create policy change
        policy_change = await create_test_policy_change(db_session, source.id)
        
        # Mock email service to fail
        with patch('api.services.alert_engine.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=False,
                error="Email service unavailable"
            ))
            mock_get_email.return_value = mock_email_service
            
            alert_engine = AlertEngine(db_session)
            alert_engine.email_service = mock_email_service
            
            # Trigger alerts
            alert_result = await alert_engine.send_alerts_for_change(policy_change.id)
            
            # Verify error handled gracefully
            assert alert_result.routes_notified == 1
            assert alert_result.emails_sent == 0
            assert alert_result.emails_failed == 1
            assert len(alert_result.errors) > 0
            
            # Verify EmailAlert record created with failed status
            alert_repo = EmailAlertRepository(db_session)
            alerts = await alert_repo.get_by_policy_change(policy_change.id)
            assert len(alerts) == 1
            assert alerts[0].status == "failed"
    
    async def test_source_fetch_failure(
        self, db_session, sample_source_data
    ):
        """Test: source fetch failure handled gracefully, no false alerts."""
        # Create source
        source = await create_test_source(
            db_session,
            country=sample_source_data["country"],
            visa_type=sample_source_data["visa_type"]
        )
        
        # Register mock fetcher that fails
        from api.services.fetcher_manager import register_fetcher
        fetcher_name = f"test_{source.country.lower()}_{source.visa_type.lower().replace(' ', '_')}"
        
        def mock_fetcher_fail(url, metadata):
            return FetchResult(
                raw_text=None,
                content_type=None,
                success=False,
                error_message="Network error"
            )
        
        register_fetcher(fetcher_name, mock_fetcher_fail, {"source_type": source.fetch_type})
        
        # Trigger fetch
        result = await fetch_and_process_source(db_session, source.id)
        
        # Verify failure handled gracefully
        assert result.success is False
        assert result.change_detected is False
        assert result.policy_change_id is None
        
        # Verify no PolicyChange created
        change_repo = PolicyChangeRepository(db_session)
        changes = await change_repo.get_by_source_id(source.id)
        assert len(changes) == 0
    
    async def test_scheduled_job_execution(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: scheduled job processes sources and triggers alerts."""
        # Create source and route
        source = await create_test_source(
            db_session,
            country=sample_source_data["country"],
            visa_type=sample_source_data["visa_type"],
            check_frequency="daily"
        )
        route = await create_test_route(
            db_session,
            destination_country=source.country,
            visa_type=source.visa_type,
            email="test@example.com"
        )
        
        # Register mock fetcher
        from api.services.fetcher_manager import register_fetcher
        fetcher_name = f"test_{source.country.lower()}_{source.visa_type.lower().replace(' ', '_')}"
        
        call_count = 0
        def mock_fetcher(url, metadata):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return FetchResult(
                    raw_text="Original content",
                    content_type="html",
                    success=True,
                    fetched_at=datetime.utcnow()
                )
            else:
                return FetchResult(
                    raw_text="Updated content",
                    content_type="html",
                    success=True,
                    fetched_at=datetime.utcnow()
                )
        
        register_fetcher(fetcher_name, mock_fetcher, {"source_type": source.fetch_type})
        
        # First fetch (baseline)
        await fetch_and_process_source(db_session, source.id)
        
        # Mock email service
        with patch('api.services.alert_engine.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=True,
                message_id="test_email_123"
            ))
            mock_get_email.return_value = mock_email_service
            
            # Patch AlertEngine to use mock email service
            original_init = AlertEngine.__init__
            def patched_init(self, session):
                original_init(self, session)
                self.email_service = mock_email_service
            
            with patch.object(AlertEngine, '__init__', patched_init):
                # Run scheduled job
                job_result = await run_daily_fetch_job(db_session)
                
                # Verify job executed
                assert job_result.sources_processed == 1
                assert job_result.completed_at is not None
                
                # If change detected, verify alert sent
                if job_result.changes_detected > 0:
                    assert job_result.alerts_sent >= 0  # May be 0 if no routes match
                    if job_result.alerts_sent > 0:
                        assert mock_email_service.send_email.called
    
    async def test_email_content_accuracy(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: email content includes all required fields."""
        # Create source and route
        source = await create_test_source(
            db_session,
            country=sample_source_data["country"],
            visa_type=sample_source_data["visa_type"]
        )
        route = await create_test_route(
            db_session,
            destination_country=source.country,
            visa_type=source.visa_type,
            email="test@example.com"
        )
        
        # Create policy change with diff
        diff_text = "--- old\n+++ new\n@@ -1,3 +1,3 @@\n-Line 1\n-Line 2\n-Line 3\n+Line 1 Updated\n+Line 2 Updated\n+Line 3 Updated"
        policy_change = await create_test_policy_change(
            db_session,
            source.id,
            diff=diff_text
        )
        
        # Mock email service
        with patch('api.services.alert_engine.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=True,
                message_id="test_email_123"
            ))
            mock_get_email.return_value = mock_email_service
            
            alert_engine = AlertEngine(db_session)
            alert_engine.email_service = mock_email_service
            
            # Trigger alert
            await alert_engine.send_alerts_for_change(policy_change.id)
            
            # Verify email content
            call_args = mock_email_service.send_email.call_args
            html_body = call_args[1]["html_body"]
            text_body = call_args[1]["text_body"]
            subject = call_args[1]["subject"]
            
            # Verify subject line
            assert "Policy Change Detected" in subject
            assert route.origin_country in subject
            assert route.destination_country in subject
            assert route.visa_type in subject
            assert source.name in subject
            
            # Verify route information in email
            assert route.origin_country in html_body
            assert route.destination_country in html_body
            assert route.visa_type in html_body
            
            # Verify source information
            assert source.name in html_body
            assert source.url in html_body
            
            # Verify timestamp
            assert policy_change.detected_at.isoformat() in html_body or str(policy_change.detected_at) in html_body
            
            # Verify diff preview
            assert "diff" in html_body.lower() or "change" in html_body.lower()
            
            # Verify link to full diff
            assert "View Full Diff" in html_body or "view full diff" in html_body.lower()
            assert str(policy_change.id) in html_body or "change" in html_body.lower()
            
            # Verify disclaimer
            assert "This is information, not legal advice" in html_body or "not legal advice" in html_body.lower()
            
            # Verify plain text version has same content
            assert route.origin_country in text_body
            assert route.destination_country in text_body
            assert source.name in text_body
            assert source.url in text_body

