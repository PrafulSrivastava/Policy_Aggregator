"""Unit tests for UK Home Office Immigration Rules fetcher."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fetchers.uk_home_office_immigration_rules import fetch
from fetchers.base import FetchResult


class TestUKHomeOfficeImmigrationRulesFetcher:
    """Tests for UK Home Office Immigration Rules fetcher."""
    
    @patch('fetchers.uk_home_office_immigration_rules.fetch_html')
    def test_successful_fetch(self, mock_fetch_html):
        """Test successful fetch with metadata addition."""
        mock_result = FetchResult(
            raw_text="Immigration rules guidance content here.",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={
                "country": "UK",
                "visa_type": "Both",
                "page_title": "Immigration Rules - GOV.UK"
            },
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "UK", "visa_type": "Both", "fetch_type": "html"}
        result = fetch("https://www.gov.uk/guidance/immigration-rules", metadata)
        
        assert result.success is True
        assert result.content_type == "html"
        assert "Immigration rules guidance content here." in result.raw_text
        assert result.metadata['source'] == 'UK Home Office'
        assert result.metadata['agency'] == 'UKVI'
        assert result.metadata['visa_category'] == 'Both'
        assert result.metadata['route'] == 'India → UK'
        assert result.metadata['content_scope'] == 'Immigration Rules Guidance'
    
    @patch('fetchers.uk_home_office_immigration_rules.fetch_html')
    def test_visa_type_from_metadata(self, mock_fetch_html):
        """Test that visa_category uses metadata visa_type."""
        mock_result = FetchResult(
            raw_text="Content",
            content_type="html",
            fetched_at=datetime.utcnow(),
            metadata={"country": "UK"},
            success=True
        )
        mock_fetch_html.return_value = mock_result
        
        metadata = {"country": "UK", "visa_type": "Student", "fetch_type": "html"}
        result = fetch("https://www.gov.uk/guidance/immigration-rules", metadata)
        
        assert result.metadata['visa_category'] == 'Student'

