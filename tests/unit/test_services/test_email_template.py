"""Unit tests for email template service."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch
from api.services.email_template import EmailTemplateService, EmailContent
from api.models.db.policy_change import PolicyChange
from api.models.db.route_subscription import RouteSubscription
from api.models.db.source import Source


@pytest.fixture
def sample_policy_change():
    """Sample PolicyChange instance for testing."""
    change = Mock(spec=PolicyChange)
    change.id = uuid.uuid4()
    change.diff = "--- old\n+++ new\n@@ -1,3 +1,3 @@\n Line 1\n-Line 2 (removed)\n+Line 2 (added)\n Line 3"
    change.detected_at = datetime(2025, 1, 27, 10, 30, 0)
    return change


@pytest.fixture
def sample_route_subscription():
    """Sample RouteSubscription instance for testing."""
    route = Mock(spec=RouteSubscription)
    route.origin_country = "IN"
    route.destination_country = "DE"
    route.visa_type = "Student"
    route.email = "test@example.com"
    return route


@pytest.fixture
def sample_source():
    """Sample Source instance for testing."""
    source = Mock(spec=Source)
    source.name = "Germany BMI"
    source.url = "https://example.com/germany-student-visa"
    source.country = "DE"
    source.visa_type = "Student"
    return source


@pytest.fixture
def email_template_service(tmp_path):
    """Create EmailTemplateService with temporary template directory."""
    # Create temporary template files
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    
    html_template = template_dir / "change_alert.html"
    html_template.write_text("""
    <html>
    <body>
        <h1>Policy Change Detected</h1>
        <p>Route: {{ route.origin_country }} → {{ route.destination_country }}, {{ route.visa_type }} Visa</p>
        <p>Source: {{ source.name }}</p>
        <p>URL: {{ source.url }}</p>
        <p>Detected: {{ detected_at.strftime('%B %d, %Y at %I:%M %p UTC') }}</p>
        <pre>{{ diff_preview }}</pre>
        <a href="{{ admin_ui_url }}/changes/{{ change_id }}">View Full Diff</a>
        <p>Disclaimer: This is information, not legal advice.</p>
    </body>
    </html>
    """)
    
    text_template = template_dir / "change_alert.txt"
    text_template.write_text("""
POLICY CHANGE DETECTED
======================
Route: {{ route.origin_country }} → {{ route.destination_country }}, {{ route.visa_type }} Visa
Source: {{ source.name }}
URL: {{ source.url }}
Detected: {{ detected_at.strftime('%B %d, %Y at %I:%M %p UTC') }}
{{ diff_preview }}
View Full Diff: {{ admin_ui_url }}/changes/{{ change_id }}
Disclaimer: This is information, not legal advice.
    """)
    
    return EmailTemplateService(template_dir=str(template_dir))


class TestEmailTemplateService:
    """Tests for EmailTemplateService."""
    
    def test_generate_email_subject(self, email_template_service, sample_route_subscription, sample_source):
        """Test that email subject is generated correctly."""
        subject = email_template_service.generate_email_subject(
            sample_route_subscription,
            sample_source
        )
        
        assert "Policy Change Detected" in subject
        assert "IN" in subject
        assert "DE" in subject
        assert "Student" in subject
        assert "Germany BMI" in subject
        assert subject == "Policy Change Detected: IN → DE, Student Visa - Germany BMI"
    
    def test_generate_diff_preview_truncates_at_char_limit(self, email_template_service):
        """Test that diff preview truncates at character limit."""
        long_diff = "a" * 1000
        preview = email_template_service.generate_diff_preview(long_diff, max_chars=500, max_lines=100)
        
        assert len(preview) == 503  # 500 chars + "..."
        assert preview.endswith("...")
    
    def test_generate_diff_preview_truncates_at_line_limit(self, email_template_service):
        """Test that diff preview truncates at line limit."""
        many_lines = "\n".join([f"Line {i}" for i in range(50)])
        preview = email_template_service.generate_diff_preview(many_lines, max_chars=10000, max_lines=20)
        
        lines = preview.split('\n')
        assert len(lines) == 21  # 20 lines + "..."
        assert preview.endswith("...")
    
    def test_generate_diff_preview_preserves_short_diff(self, email_template_service):
        """Test that short diff is preserved without truncation."""
        short_diff = "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Line 1\n+Line 2"
        preview = email_template_service.generate_diff_preview(short_diff)
        
        assert preview == short_diff
        assert not preview.endswith("...")
    
    def test_generate_diff_preview_handles_empty_diff(self, email_template_service):
        """Test that empty diff is handled gracefully."""
        preview = email_template_service.generate_diff_preview("")
        
        assert preview == "(No changes shown)"
    
    def test_render_change_alert_template_renders_html(self, email_template_service, sample_policy_change, sample_route_subscription, sample_source):
        """Test that HTML template is rendered correctly."""
        email_content = email_template_service.render_change_alert_template(
            sample_policy_change,
            sample_route_subscription,
            sample_source,
            admin_ui_url="http://localhost:9000"
        )
        
        assert isinstance(email_content, EmailContent)
        assert email_content.html_body is not None
        assert "<html>" in email_content.html_body
        assert "Policy Change Detected" in email_content.html_body
        assert "IN → DE" in email_content.html_body
        assert "Student" in email_content.html_body
        assert "Germany BMI" in email_content.html_body
        assert "http://localhost:8000" in email_content.html_body
        assert str(sample_policy_change.id) in email_content.html_body
    
    def test_render_change_alert_template_renders_text(self, email_template_service, sample_policy_change, sample_route_subscription, sample_source):
        """Test that plain text template is rendered correctly."""
        email_content = email_template_service.render_change_alert_template(
            sample_policy_change,
            sample_route_subscription,
            sample_source,
            admin_ui_url="http://localhost:9000"
        )
        
        assert email_content.text_body is not None
        assert "POLICY CHANGE DETECTED" in email_content.text_body
        assert "IN → DE" in email_content.text_body
        assert "Student" in email_content.text_body
        assert "Germany BMI" in email_content.text_body
        assert "http://localhost:8000" in email_content.text_body
        assert str(sample_policy_change.id) in email_content.text_body
    
    def test_render_change_alert_template_includes_all_placeholders(self, email_template_service, sample_policy_change, sample_route_subscription, sample_source):
        """Test that all template placeholders are filled."""
        email_content = email_template_service.render_change_alert_template(
            sample_policy_change,
            sample_route_subscription,
            sample_source
        )
        
        # Check HTML contains all required elements
        assert sample_route_subscription.origin_country in email_content.html_body
        assert sample_route_subscription.destination_country in email_content.html_body
        assert sample_route_subscription.visa_type in email_content.html_body
        assert sample_source.name in email_content.html_body
        assert sample_source.url in email_content.html_body
        assert "View Full Diff" in email_content.html_body or "view full diff" in email_content.html_body.lower()
        assert "This is information, not legal advice" in email_content.html_body
        
        # Check text contains all required elements
        assert sample_route_subscription.origin_country in email_content.text_body
        assert sample_route_subscription.destination_country in email_content.text_body
        assert sample_route_subscription.visa_type in email_content.text_body
        assert sample_source.name in email_content.text_body
        assert sample_source.url in email_content.text_body
        assert "This is information, not legal advice" in email_content.text_body
    
    def test_render_change_alert_template_generates_subject(self, email_template_service, sample_policy_change, sample_route_subscription, sample_source):
        """Test that subject line is generated correctly."""
        email_content = email_template_service.render_change_alert_template(
            sample_policy_change,
            sample_route_subscription,
            sample_source
        )
        
        assert email_content.subject is not None
        assert "Policy Change Detected" in email_content.subject
        assert sample_route_subscription.origin_country in email_content.subject
        assert sample_route_subscription.destination_country in email_content.subject
        assert sample_route_subscription.visa_type in email_content.subject
        assert sample_source.name in email_content.subject
    
    def test_render_change_alert_template_uses_provided_diff_preview(self, email_template_service, sample_policy_change, sample_route_subscription, sample_source):
        """Test that provided diff preview is used instead of generating one."""
        custom_preview = "Custom diff preview text"
        email_content = email_template_service.render_change_alert_template(
            sample_policy_change,
            sample_route_subscription,
            sample_source,
            diff_preview=custom_preview
        )
        
        assert custom_preview in email_content.html_body
        assert custom_preview in email_content.text_body
    
    def test_render_change_alert_template_uses_provided_admin_ui_url(self, email_template_service, sample_policy_change, sample_route_subscription, sample_source):
        """Test that provided admin UI URL is used."""
        custom_url = "https://custom-admin.example.com"
        email_content = email_template_service.render_change_alert_template(
            sample_policy_change,
            sample_route_subscription,
            sample_source,
            admin_ui_url=custom_url
        )
        
        assert custom_url in email_content.html_body
        assert custom_url in email_content.text_body
    
    def test_render_change_alert_template_handles_missing_template(self, tmp_path):
        """Test that missing template raises TemplateNotFound."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        # Don't create template files
        
        service = EmailTemplateService(template_dir=str(template_dir))
        
        with pytest.raises(Exception):  # TemplateNotFound or similar
            service.render_change_alert_template(
                Mock(spec=PolicyChange),
                Mock(spec=RouteSubscription),
                Mock(spec=Source)
            )
    
    def test_render_change_alert_template_handles_special_characters(self, email_template_service):
        """Test that special characters in data are handled correctly."""
        change = Mock(spec=PolicyChange)
        change.id = uuid.uuid4()
        change.diff = "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Line with <special> & characters"
        change.detected_at = datetime(2025, 1, 27, 10, 30, 0)
        
        route = Mock(spec=RouteSubscription)
        route.origin_country = "IN"
        route.destination_country = "DE"
        route.visa_type = "Student"
        route.email = "test@example.com"
        
        source = Mock(spec=Source)
        source.name = "Source with <special> & characters"
        source.url = "https://example.com/path?param=value&other=test"
        source.country = "DE"
        source.visa_type = "Student"
        
        email_content = email_template_service.render_change_alert_template(
            change,
            route,
            source
        )
        
        # Should render without errors
        assert email_content.html_body is not None
        assert email_content.text_body is not None
        assert "Source with" in email_content.html_body or "Source with" in email_content.text_body

