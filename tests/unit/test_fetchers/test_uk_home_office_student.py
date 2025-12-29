"""Unit tests for UK Home Office Student visa fetcher."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fetchers.uk_home_office_student import fetch
from fetchers.base import FetchResult


class TestUKHomeOfficeStudentFetcher:
    """Tests for UK Home Office Student visa fetcher."""
    
    @patch('fetchers.uk_home_office_student.fetch_html')
    def test_successful_fetch(self, mock_fetch_html):
        """Test successful fetch with metadata addition."""
        # Mock successful fetch_html result
        mock_result = FetchResult(
            raw_text="Student visa information content here.",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={
                "country": "UK",
                "visa_type": "Student",
                "page_title": "Student visa - GOV.UK"
            },
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "UK", "visa_type": "Student", "fetch_type": "html"}
        result = fetch("https://www.gov.uk/student-visa", metadata)
        
        assert result.success is True
        assert result.content_type == "html"
        assert "Student visa information content here." in result.raw_text
        assert result.metadata['source'] == 'UK Home Office'
        assert result.metadata['agency'] == 'UKVI'
        assert result.metadata['visa_category'] == 'Student'
        assert result.metadata['route'] == 'India → UK'
        mock_fetch_html.assert_called_once_with("https://www.gov.uk/student-visa", metadata)
    
    @patch('fetchers.uk_home_office_student.fetch_html')
    def test_fetch_error_handling(self, mock_fetch_html):
        """Test error handling when fetch_html fails."""
        # Mock failed fetch_html result
        mock_result = FetchResult(
            raw_text="",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={},
            success=False,
            error_message="network_error: Connection timeout"
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "UK", "visa_type": "Student", "fetch_type": "html"}
        result = fetch("https://www.gov.uk/student-visa", metadata)
        
        assert result.success is False
        assert result.error_message == "network_error: Connection timeout"
        # Should not add source-specific metadata on failure
        assert 'source' not in result.metadata
        mock_fetch_html.assert_called_once_with("https://www.gov.uk/student-visa", metadata)
    
    @patch('fetchers.uk_home_office_student.fetch_html')
    def test_metadata_preservation(self, mock_fetch_html):
        """Test that original metadata is preserved and extended."""
        # Mock successful fetch_html result with existing metadata
        mock_result = FetchResult(
            raw_text="Content",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={
                "country": "UK",
                "visa_type": "Student",
                "page_title": "Student visa",
                "last_modified": "2025-01-27"
            },
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "UK", "visa_type": "Student"}
        result = fetch("https://www.gov.uk/student-visa", metadata)
        
        # Original metadata should be preserved
        assert result.metadata['page_title'] == "Student visa"
        assert result.metadata['last_modified'] == "2025-01-27"
        # New metadata should be added
        assert result.metadata['source'] == 'UK Home Office'
        assert result.metadata['agency'] == 'UKVI'
        assert result.metadata['visa_category'] == 'Student'
        assert result.metadata['route'] == 'India → UK'

