"""
IRCC Study Permit policy fetcher.

This fetcher monitors the official Canadian government website for study permit information.
Source: https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit.html

Monitors study permit requirements and policy changes for India → Canada route.
"""

import logging
from typing import Dict, Any
from fetchers.base import FetchResult
from fetchers.html_fetcher import fetch_html

logger = logging.getLogger(__name__)

# Source type for fetcher manager matching
SOURCE_TYPE = "html"


def fetch(url: str, metadata: Dict[str, Any]) -> FetchResult:
    """
    Fetch study permit policy content from IRCC website.
    
    Args:
        url: URL to the study permit information page
        metadata: Source metadata including:
            - country: "CA"
            - visa_type: "Student"
            - fetch_type: "html"
            - Any other source-specific configuration
    
    Returns:
        FetchResult with fetched content or error information
    """
    # Use the HTML fetcher utilities
    result = fetch_html(url, metadata)
    
    # Add source-specific metadata if needed
    if result.success:
        result.metadata['source'] = 'IRCC'
        result.metadata['agency'] = 'Immigration, Refugees and Citizenship Canada'
        result.metadata['visa_category'] = 'Student'
        result.metadata['visa_subtype'] = 'Study Permit'
        result.metadata['route'] = 'India → Canada'
        logger.info(f"Successfully fetched study permit content from {url} ({len(result.raw_text)} chars)")
    else:
        logger.error(f"Failed to fetch study permit content from {url}: {result.error_message}")
    
    return result

