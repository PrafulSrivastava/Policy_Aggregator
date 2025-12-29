"""Email template rendering service.

This service provides functionality to render email templates for policy change alerts,
including HTML and plain text versions, subject line generation, and diff preview generation.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound

from api.config import settings
from api.models.db.policy_change import PolicyChange
from api.models.db.route_subscription import RouteSubscription
from api.models.db.source import Source

logger = logging.getLogger(__name__)


@dataclass
class EmailContent:
    """Email content with HTML and plain text versions."""
    subject: str
    html_body: str
    text_body: str


class EmailTemplateService:
    """Service for rendering email templates."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize email template service.
        
        Args:
            template_dir: Directory containing email templates (defaults to config)
        """
        self.template_dir = template_dir or settings.EMAIL_TEMPLATE_DIR
        
        # Create Jinja2 environment
        if not os.path.exists(self.template_dir):
            logger.warning(f"Template directory not found: {self.template_dir}")
        
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate_email_subject(
        self,
        route: RouteSubscription,
        source: Source
    ) -> str:
        """
        Generate email subject line for policy change alert.
        
        Format: "Policy Change Detected: {origin} → {destination}, {visa_type} - {source_name}"
        Example: "Policy Change Detected: India → Germany, Student Visa - Germany BMI"
        
        Args:
            route: RouteSubscription instance
            source: Source instance
            
        Returns:
            Formatted subject line string
        """
        subject = (
            f"Policy Change Detected: {route.origin_country} → "
            f"{route.destination_country}, {route.visa_type} Visa - {source.name}"
        )
        return subject
    
    def generate_diff_preview(
        self,
        diff: str,
        max_chars: int = 500,
        max_lines: int = 20
    ) -> str:
        """
        Generate a preview of the diff text.
        
        Extracts first max_chars characters or first max_lines lines (whichever comes first).
        Adds ellipsis if diff is truncated.
        Preserves diff format (unified diff format).
        
        Args:
            diff: Full diff text
            max_chars: Maximum characters to include
            max_lines: Maximum lines to include
            max_lines: Maximum lines to include
            
        Returns:
            Truncated diff preview with ellipsis if needed
        """
        if not diff:
            return "(No changes shown)"
        
        lines = diff.split('\n')
        
        # Check line limit first
        if len(lines) > max_lines:
            preview_lines = lines[:max_lines]
            preview = '\n'.join(preview_lines)
            if len(preview) > max_chars:
                preview = preview[:max_chars]
            return preview + '\n...'
        
        # Check character limit
        if len(diff) > max_chars:
            return diff[:max_chars] + '...'
        
        return diff
    
    def render_change_alert_template(
        self,
        change: PolicyChange,
        route: RouteSubscription,
        source: Source,
        diff_preview: Optional[str] = None,
        admin_ui_url: Optional[str] = None
    ) -> EmailContent:
        """
        Render change alert email template.
        
        Renders both HTML and plain text versions of the email template with all
        required placeholders filled in.
        
        Args:
            change: PolicyChange instance
            route: RouteSubscription instance
            source: Source instance
            diff_preview: Optional diff preview (if None, will be generated)
            admin_ui_url: Optional admin UI URL (defaults to config)
            
        Returns:
            EmailContent with subject, HTML body, and plain text body
            
        Raises:
            TemplateNotFound: If template files are not found
            Exception: If template rendering fails
        """
        # Generate diff preview if not provided
        if diff_preview is None:
            diff_preview = self.generate_diff_preview(change.diff)
        
        # Use configured admin UI URL if not provided
        admin_url = admin_ui_url or settings.ADMIN_UI_URL
        
        # Prepare template context
        context = {
            'change': change,
            'change_id': str(change.id),
            'route': route,
            'source': source,
            'detected_at': change.detected_at,
            'diff_preview': diff_preview,
            'admin_ui_url': admin_url
        }
        
        try:
            # Render HTML template
            html_template = self.env.get_template('change_alert.html')
            html_body = html_template.render(**context)
        except TemplateNotFound:
            logger.error(f"HTML template not found: change_alert.html in {self.template_dir}")
            raise
        except Exception as e:
            logger.error(f"Error rendering HTML template: {e}", exc_info=True)
            raise
        
        try:
            # Render plain text template
            text_template = self.env.get_template('change_alert.txt')
            text_body = text_template.render(**context)
        except TemplateNotFound:
            logger.error(f"Text template not found: change_alert.txt in {self.template_dir}")
            raise
        except Exception as e:
            logger.error(f"Error rendering text template: {e}", exc_info=True)
            raise
        
        # Generate subject line
        subject = self.generate_email_subject(route, source)
        
        return EmailContent(
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )

