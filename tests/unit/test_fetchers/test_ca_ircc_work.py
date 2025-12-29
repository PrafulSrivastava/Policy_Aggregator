"""Unit tests for IRCC Work Permit fetcher."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fetchers.ca_ircc_work import fetch
from fetchers.base import FetchResult


class TestCAIRCCWorkFetcher:
    """Tests for IRCC Work Permit fetcher."""
    
    @patch('fetchers.ca_ircc_work.fetch_html')
    def test_successful_fetch(self, mock_fetch_html):
        """Test successful fetch with metadata addition."""
        mock_result = FetchResult(
            raw_text="Work permit information content here.",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={
                "country": "CA",
                "visa_type": "Work",
                "page_title": "Work in Canada - Canada.ca"
            },
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "CA", "visa_type": "Work", "fetch_type": "html"}
        result = fetch("https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada.html", metadata)
        
        assert result.success is True
        assert result.content_type == "html"
        assert "Work permit information content here." in result.raw_text
        assert result.metadata['source'] == 'IRCC'
        assert result.metadata['agency'] == 'Immigration, Refugees and Citizenship Canada'
        assert result.metadata['visa_category'] == 'Work'
        assert result.metadata['visa_subtype'] == 'Work Permit'
        assert result.metadata['route'] == 'India → Canada'
    
    @patch('fetchers.ca_ircc_work.fetch_html')
    def test_fetch_error_handling(self, mock_fetch_html):
        """Test error handling when fetch_html fails."""
        mock_result = FetchResult(
            raw_text="",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={},
            success=False,
            error_message="network_error: Connection refused"
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "CA", "visa_type": "Work", "fetch_type": "html"}
        result = fetch("https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada.html", metadata)
        
        assert result.success is False
        assert result.error_message == "network_error: Connection refused"
        assert 'source' not in result.metadata

