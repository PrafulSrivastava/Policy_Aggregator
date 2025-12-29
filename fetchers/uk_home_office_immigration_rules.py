"""
UK Home Office Immigration Rules policy fetcher.

This fetcher monitors the official UK government website for immigration rules guidance.
Source: https://www.gov.uk/guidance/immigration-rules

Monitors immigration rules and policy changes for India → UK route (covers both Student and Work visas).
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
    Fetch immigration rules policy content from UK Home Office website.
    
    Args:
        url: URL to the immigration rules guidance page (typically https://www.gov.uk/guidance/immigration-rules)
        metadata: Source metadata including:
            - country: "UK" or "GB"
            - visa_type: "Student", "Work", or "Both"
            - fetch_type: "html"
            - Any other source-specific configuration
    
    Returns:
        FetchResult with fetched content or error information
    
    Note:
        This source covers both Student and Work visa types. The page may contain links to PDF documents
        which are not automatically followed. The HTML content provides comprehensive guidance on immigration rules.
    """
    # Use the HTML fetcher utilities
    result = fetch_html(url, metadata)
    
    # Add source-specific metadata if needed
    if result.success:
        result.metadata['source'] = 'UK Home Office'
        result.metadata['agency'] = 'UKVI'
        result.metadata['visa_category'] = metadata.get('visa_type', 'Both')
        result.metadata['route'] = 'India → UK'
        result.metadata['content_scope'] = 'Immigration Rules Guidance'
        logger.info(f"Successfully fetched immigration rules content from {url} ({len(result.raw_text)} chars)")
    else:
        logger.error(f"Failed to fetch immigration rules content from {url}: {result.error_message}")
    
    return result

