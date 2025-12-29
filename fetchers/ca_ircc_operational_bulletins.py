"""
IRCC Operational Bulletins and Manuals policy fetcher.

This fetcher monitors the official Canadian government website for operational bulletins and manuals.
Source: https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals.html

Monitors operational instructions and policy implementation details for India → Canada route (covers both Student and Work visas).
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
    Fetch operational bulletins and manuals content from IRCC website.
    
    Args:
        url: URL to the operational bulletins and manuals page
        metadata: Source metadata including:
            - country: "CA"
            - visa_type: "Student", "Work", or "Both"
            - fetch_type: "html"
            - Any other source-specific configuration
    
    Returns:
        FetchResult with fetched content or error information
    
    Note:
        This source covers both Student and Work visa types. The page contains links to detailed
        operational instructions (HTML and PDF). The HTML content provides comprehensive guidance on
        policy implementation. PDF links are not automatically followed.
    """
    # Use the HTML fetcher utilities
    result = fetch_html(url, metadata)
    
    # Add source-specific metadata if needed
    if result.success:
        result.metadata['source'] = 'IRCC'
        result.metadata['agency'] = 'Immigration, Refugees and Citizenship Canada'
        result.metadata['visa_category'] = metadata.get('visa_type', 'Both')
        result.metadata['route'] = 'India → Canada'
        result.metadata['content_scope'] = 'Operational Bulletins and Manuals'
        logger.info(f"Successfully fetched operational bulletins content from {url} ({len(result.raw_text)} chars)")
    else:
        logger.error(f"Failed to fetch operational bulletins content from {url}: {result.error_message}")
    
    return result

