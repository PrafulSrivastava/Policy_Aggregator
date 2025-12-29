"""
Germany BAMF (Bundesamt für Migration und Flüchtlinge) Work visa policy fetcher.

This fetcher monitors the official German Federal Office for Migration and Refugees website
for immigration procedures, residence permits, and work-related immigration information.
Source: https://www.bamf.de

Monitors work visa requirements, residence permits, and immigration procedures for India → Germany route.
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
    Fetch work visa policy content from Germany BAMF website.
    
    Args:
        url: URL to the work visa/immigration policy page
        metadata: Source metadata including:
            - country: "DE"
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
        result.metadata['source'] = 'Germany BAMF'
        result.metadata['visa_category'] = 'Work'
        result.metadata['route'] = 'India → Germany'
        logger.info(f"Successfully fetched work visa content from BAMF {url} ({len(result.raw_text)} chars)")
    else:
        logger.error(f"Failed to fetch work visa content from BAMF {url}: {result.error_message}")
    
    return result

