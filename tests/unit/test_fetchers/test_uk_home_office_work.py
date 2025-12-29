"""Unit tests for UK Home Office Skilled Worker visa fetcher."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fetchers.uk_home_office_work import fetch
from fetchers.base import FetchResult


class TestUKHomeOfficeWorkFetcher:
    """Tests for UK Home Office Skilled Worker visa fetcher."""
    
    @patch('fetchers.uk_home_office_work.fetch_html')
    def test_successful_fetch(self, mock_fetch_html):
        """Test successful fetch with metadata addition."""
        mock_result = FetchResult(
            raw_text="Skilled worker visa information content here.",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={
                "country": "UK",
                "visa_type": "Work",
                "page_title": "Skilled Worker visa - GOV.UK"
            },
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "UK", "visa_type": "Work", "fetch_type": "html"}
        result = fetch("https://www.gov.uk/skilled-worker-visa", metadata)
        
        assert result.success is True
        assert result.content_type == "html"
        assert "Skilled worker visa information content here." in result.raw_text
        assert result.metadata['source'] == 'UK Home Office'
        assert result.metadata['agency'] == 'UKVI'
        assert result.metadata['visa_category'] == 'Work'
        assert result.metadata['visa_subtype'] == 'Skilled Worker'
        assert result.metadata['route'] == 'India → UK'
    
    @patch('fetchers.uk_home_office_work.fetch_html')
    def test_fetch_error_handling(self, mock_fetch_html):
        """Test error handling when fetch_html fails."""
        mock_result = FetchResult(
            raw_text="",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={},
            success=False,
            error_message="not_found_error: HTTP 404 - Not Found"
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "UK", "visa_type": "Work", "fetch_type": "html"}
        result = fetch("https://www.gov.uk/skilled-worker-visa", metadata)
        
        assert result.success is False
        assert result.error_message == "not_found_error: HTTP 404 - Not Found"
        assert 'source' not in result.metadata

