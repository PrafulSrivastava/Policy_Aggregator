"""Integration tests for alert engine service."""

import pytest
from datetime import datetime
from api.services.alert_engine import AlertEngine
from api.repositories.policy_change_repository import PolicyChangeRepository
from api.repositories.source_repository import SourceRepository
from api.repositories.route_subscription_repository import RouteSubscriptionRepository
from api.repositories.email_alert_repository import EmailAlertRepository
from api.services.route_mapper import RouteMapper
from unittest.mock import Mock, patch


@pytest.mark.asyncio
class TestAlertEngineIntegration:
    """Integration tests for AlertEngine service."""
    
    async def test_send_alerts_for_change_full_flow(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test full flow: create change, verify emails sent to matching routes."""
        # Create source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create route subscription
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Create policy change
        change_repo = PolicyChangeRepository(db_session)
        change_data = {
            "source_id": source.id,
            "old_hash": "a" * 64,
            "new_hash": "b" * 64,
            "diff": "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Line 1\n+Line 2",
            "detected_at": datetime.utcnow(),
            "new_version_id": None,  # Would normally be a PolicyVersion ID
            "diff_length": 50
        }
        policy_change = await change_repo.create(change_data)
        
        # Mock email service to avoid sending real emails
        with patch('api.services.alert_engine.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=True,
                message_id="test_email_123"
            ))
            mock_get_email.return_value = mock_email_service
            
            # Create alert engine and send alerts
            alert_engine = AlertEngine(db_session)
            alert_engine.email_service = mock_email_service
            
            result = await alert_engine.send_alerts_for_change(policy_change.id)
            
            # Verify result
            assert result.policy_change_id == policy_change.id
            assert result.routes_notified == 1
            assert result.emails_sent == 1
            assert result.emails_failed == 0
            
            # Verify email was sent
            mock_email_service.send_email.assert_called_once()
            call_kwargs = mock_email_service.send_email.call_args[1]
            assert call_kwargs['recipient'] == route.email
            assert "Policy Change Detected" in call_kwargs['subject']
            
            # Verify EmailAlert record was created
            alert_repo = EmailAlertRepository(db_session)
            alerts = await alert_repo.get_by_policy_change(policy_change.id)
            assert len(alerts) == 1
            assert alerts[0].route_subscription_id == route.id
            assert alerts[0].status == "sent"
            assert alerts[0].email_provider_id == "test_email_123"
    
    async def test_send_alerts_multiple_routes_match_one_source(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test: multiple routes match one source."""
        # Create source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create multiple route subscriptions
        route_repo = RouteSubscriptionRepository(db_session)
        
        route1_data = sample_route_subscription_data.copy()
        route1_data["email"] = "user1@example.com"
        route1 = await route_repo.create(route1_data)
        
        route2_data = sample_route_subscription_data.copy()
        route2_data["email"] = "user2@example.com"
        route2 = await route_repo.create(route2_data)
        
        route3_data = sample_route_subscription_data.copy()
        route3_data["email"] = "user3@example.com"
        route3 = await route_repo.create(route3_data)
        
        # Create policy change
        change_repo = PolicyChangeRepository(db_session)
        change_data = {
            "source_id": source.id,
            "old_hash": "a" * 64,
            "new_hash": "b" * 64,
            "diff": "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Line 1\n+Line 2",
            "detected_at": datetime.utcnow(),
            "new_version_id": None,
            "diff_length": 50
        }
        policy_change = await change_repo.create(change_data)
        
        # Mock email service
        with patch('api.services.alert_engine.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=True,
                message_id="test_email_123"
            ))
            mock_get_email.return_value = mock_email_service
            
            # Create alert engine and send alerts
            alert_engine = AlertEngine(db_session)
            alert_engine.email_service = mock_email_service
            
            result = await alert_engine.send_alerts_for_change(policy_change.id)
            
            # Verify result
            assert result.routes_notified == 3
            assert result.emails_sent == 3
            assert result.emails_failed == 0
            
            # Verify emails were sent to all routes
            assert mock_email_service.send_email.call_count == 3
            
            # Verify EmailAlert records were created for all routes
            alert_repo = EmailAlertRepository(db_session)
            alerts = await alert_repo.get_by_policy_change(policy_change.id)
            assert len(alerts) == 3
            route_ids = {alert.route_subscription_id for alert in alerts}
            assert route1.id in route_ids
            assert route2.id in route_ids
            assert route3.id in route_ids
    
    async def test_send_alerts_no_routes_match_source(
        self, db_session, sample_source_data
    ):
        """Test: no routes match source."""
        # Create source
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        # Create route with different destination/visa_type (won't match)
        route_repo = RouteSubscriptionRepository(db_session)
        route_data = {
            "origin_country": "IN",
            "destination_country": "FR",  # Different country
            "visa_type": "Work",  # Different visa type
            "email": "test@example.com",
            "is_active": True
        }
        await route_repo.create(route_data)
        
        # Create policy change
        change_repo = PolicyChangeRepository(db_session)
        change_data = {
            "source_id": source.id,
            "old_hash": "a" * 64,
            "new_hash": "b" * 64,
            "diff": "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Line 1\n+Line 2",
            "detected_at": datetime.utcnow(),
            "new_version_id": None,
            "diff_length": 50
        }
        policy_change = await change_repo.create(change_data)
        
        # Mock email service
        with patch('api.services.alert_engine.get_email_service') as mock_get_email:
            mock_email_service = Mock()
            mock_get_email.return_value = mock_email_service
            
            # Create alert engine and send alerts
            alert_engine = AlertEngine(db_session)
            alert_engine.email_service = mock_email_service
            
            result = await alert_engine.send_alerts_for_change(policy_change.id)
            
            # Verify result
            assert result.routes_notified == 0
            assert result.emails_sent == 0
            assert result.emails_failed == 0
            
            # Verify no emails were sent
            mock_email_service.send_email.assert_not_called()
            
            # Verify no EmailAlert records were created
            alert_repo = EmailAlertRepository(db_session)
            alerts = await alert_repo.get_by_policy_change(policy_change.id)
            assert len(alerts) == 0
    
    async def test_send_alerts_email_failure_still_creates_record(
        self, db_session, sample_source_data, sample_route_subscription_data
    ):
        """Test that EmailAlert record is created even when email sending fails."""
        # Create source and route
        source_repo = SourceRepository(db_session)
        source = await source_repo.create(sample_source_data)
        
        route_repo = RouteSubscriptionRepository(db_session)
        route = await route_repo.create(sample_route_subscription_data)
        
        # Create policy change
        change_repo = PolicyChangeRepository(db_session)
        change_data = {
            "source_id": source.id,
            "old_hash": "a" * 64,
            "new_hash": "b" * 64,
            "diff": "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Line 1\n+Line 2",
            "detected_at": datetime.utcnow(),
            "new_version_id": None,
            "diff_length": 50
        }
        policy_change = await change_repo.create(change_data)
        
        # Mock email service to fail
        with patch('api.services.alert_engine.get_email_service') as mock_get_email:
            from api.integrations.resend import EmailResult
            mock_email_service = Mock()
            mock_email_service.send_email = Mock(return_value=EmailResult(
                success=False,
                error="Email send failed"
            ))
            mock_get_email.return_value = mock_email_service
            
            # Create alert engine and send alerts
            alert_engine = AlertEngine(db_session)
            alert_engine.email_service = mock_email_service
            
            result = await alert_engine.send_alerts_for_change(policy_change.id)
            
            # Verify result
            assert result.routes_notified == 1
            assert result.emails_sent == 0
            assert result.emails_failed == 1
            assert len(result.errors) == 1
            
            # Verify EmailAlert record was still created with failed status
            alert_repo = EmailAlertRepository(db_session)
            alerts = await alert_repo.get_by_policy_change(policy_change.id)
            assert len(alerts) == 1
            assert alerts[0].status == "failed"
            assert alerts[0].error_message is not None

