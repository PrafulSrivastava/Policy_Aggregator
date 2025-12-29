"""Unit tests for IRCC Study Permit fetcher."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fetchers.ca_ircc_student import fetch
from fetchers.base import FetchResult


class TestCAIRCCStudentFetcher:
    """Tests for IRCC Study Permit fetcher."""
    
    @patch('fetchers.ca_ircc_student.fetch_html')
    def test_successful_fetch(self, mock_fetch_html):
        """Test successful fetch with metadata addition."""
        mock_result = FetchResult(
            raw_text="Study permit information content here.",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={
                "country": "CA",
                "visa_type": "Student",
                "page_title": "Study permit - Canada.ca"
            },
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "CA", "visa_type": "Student", "fetch_type": "html"}
        result = fetch("https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit.html", metadata)
        
        assert result.success is True
        assert result.content_type == "html"
        assert "Study permit information content here." in result.raw_text
        assert result.metadata['source'] == 'IRCC'
        assert result.metadata['agency'] == 'Immigration, Refugees and Citizenship Canada'
        assert result.metadata['visa_category'] == 'Student'
        assert result.metadata['visa_subtype'] == 'Study Permit'
        assert result.metadata['route'] == 'India → Canada'
    
    @patch('fetchers.ca_ircc_student.fetch_html')
    def test_fetch_error_handling(self, mock_fetch_html):
        """Test error handling when fetch_html fails."""
        mock_result = FetchResult(
            raw_text="",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={},
            success=False,
            error_message="timeout_error: Request timed out after 30s"
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "CA", "visa_type": "Student", "fetch_type": "html"}
        result = fetch("https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit.html", metadata)
        
        assert result.success is False
        assert result.error_message == "timeout_error: Request timed out after 30s"
        assert 'source' not in result.metadata

