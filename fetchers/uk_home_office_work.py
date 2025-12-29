"""
UK Home Office Skilled Worker visa policy fetcher.

This fetcher monitors the official UK government website for skilled worker visa information.
Source: https://www.gov.uk/skilled-worker-visa

Monitors skilled worker visa requirements and policy changes for India → UK route.
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
    Fetch skilled worker visa policy content from UK Home Office website.
    
    Args:
        url: URL to the skilled worker visa policy page (typically https://www.gov.uk/skilled-worker-visa)
        metadata: Source metadata including:
            - country: "UK" or "GB"
            - visa_type: "Work"
            - fetch_type: "html"
            - Any other source-specific configuration
    
    Returns:
        FetchResult with fetched content or error information
    """
    # Use the HTML fetcher utilities
    result = fetch_html(url, metadata)
    
    # Add source-specific metadata if needed
    if result.success:
        result.metadata['source'] = 'UK Home Office'
        result.metadata['agency'] = 'UKVI'
        result.metadata['visa_category'] = 'Work'
        result.metadata['visa_subtype'] = 'Skilled Worker'
        result.metadata['route'] = 'India → UK'
        logger.info(f"Successfully fetched skilled worker visa content from {url} ({len(result.raw_text)} chars)")
    else:
        logger.error(f"Failed to fetch skilled worker visa content from {url}: {result.error_message}")
    
    return result

