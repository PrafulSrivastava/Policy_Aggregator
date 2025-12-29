"""Unit tests for IRCC Operational Bulletins fetcher."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fetchers.ca_ircc_operational_bulletins import fetch
from fetchers.base import FetchResult


class TestCAIRCCOperationalBulletinsFetcher:
    """Tests for IRCC Operational Bulletins fetcher."""
    
    @patch('fetchers.ca_ircc_operational_bulletins.fetch_html')
    def test_successful_fetch(self, mock_fetch_html):
        """Test successful fetch with metadata addition."""
        mock_result = FetchResult(
            raw_text="Operational bulletins and manuals content here.",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={
                "country": "CA",
                "visa_type": "Both",
                "page_title": "Operational Bulletins - Canada.ca"
            },
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "CA", "visa_type": "Both", "fetch_type": "html"}
        result = fetch("https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals.html", metadata)
        
        assert result.success is True
        assert result.content_type == "html"
        assert "Operational bulletins and manuals content here." in result.raw_text
        assert result.metadata['source'] == 'IRCC'
        assert result.metadata['agency'] == 'Immigration, Refugees and Citizenship Canada'
        assert result.metadata['visa_category'] == 'Both'
        assert result.metadata['route'] == 'India → Canada'
        assert result.metadata['content_scope'] == 'Operational Bulletins and Manuals'
    
    @patch('fetchers.ca_ircc_operational_bulletins.fetch_html')
    def test_visa_type_from_metadata(self, mock_fetch_html):
        """Test that visa_category uses metadata visa_type."""
        mock_result = FetchResult(
            raw_text="Content",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={"country": "CA"},
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "CA", "visa_type": "Work", "fetch_type": "html"}
        result = fetch("https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals.html", metadata)
        
        assert result.metadata['visa_category'] == 'Work'

