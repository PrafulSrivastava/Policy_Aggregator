"""Unit tests for Germany Bundesagentur für Arbeit Work visa fetcher."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fetchers.de_arbeitsagentur_work import fetch
from fetchers.base import FetchResult


class TestDEArbeitsagenturWorkFetcher:
    """Tests for Germany Bundesagentur für Arbeit Work visa fetcher."""
    
    @patch('fetchers.de_arbeitsagentur_work.fetch_html')
    def test_successful_fetch(self, mock_fetch_html):
        """Test successful fetch with metadata addition."""
        # Mock successful fetch_html result
        mock_result = FetchResult(
            raw_text="Bundesagentur für Arbeit work permit and employment information here.",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={
                "country": "DE",
                "visa_type": "Work",
                "page_title": "Working in Germany - Federal Employment Agency"
            },
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "DE", "visa_type": "Work", "fetch_type": "html"}
        result = fetch("https://www.arbeitsagentur.de/en/working-in-germany", metadata)
        
        assert result.success is True
        assert result.content_type == "html"
        assert "Bundesagentur für Arbeit work permit" in result.raw_text
        assert result.metadata['source'] == 'Germany Bundesagentur für Arbeit'
        assert result.metadata['visa_category'] == 'Work'
        assert result.metadata['route'] == 'India → Germany'
        mock_fetch_html.assert_called_once()
    
    @patch('fetchers.de_arbeitsagentur_work.fetch_html')
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
        
        metadata = {"country": "DE", "visa_type": "Work", "fetch_type": "html"}
        result = fetch("https://www.arbeitsagentur.de/en/working-in-germany", metadata)
        
        assert result.success is False
        assert result.error_message == "network_error: Connection timeout"
        # Should not add source-specific metadata on failure
        assert 'source' not in result.metadata
        mock_fetch_html.assert_called_once()
    
    @patch('fetchers.de_arbeitsagentur_work.fetch_html')
    def test_metadata_preservation(self, mock_fetch_html):
        """Test that original metadata is preserved and extended."""
        # Mock successful fetch_html result with existing metadata
        mock_result = FetchResult(
            raw_text="Content",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={
                "country": "DE",
                "visa_type": "Work",
                "page_title": "Working in Germany",
                "last_modified": "2025-01-27"
            },
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "DE", "visa_type": "Work"}
        result = fetch("https://www.arbeitsagentur.de/en/working-in-germany", metadata)
        
        # Original metadata should be preserved
        assert result.metadata['page_title'] == "Working in Germany"
        assert result.metadata['last_modified'] == "2025-01-27"
        # New metadata should be added
        assert result.metadata['source'] == 'Germany Bundesagentur für Arbeit'
        assert result.metadata['visa_category'] == 'Work'
        assert result.metadata['route'] == 'India → Germany'

