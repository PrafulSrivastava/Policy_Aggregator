"""
Germany DAAD (Deutscher Akademischer Austauschdienst) Student visa policy fetcher.

This fetcher monitors the official German Academic Exchange Service website for student visa information.
Source: https://www.daad.de

Monitors student visa requirements, entry requirements, and residence permits for students
for India → Germany route.
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
    Fetch student visa policy content from Germany DAAD website.
    
    Args:
        url: URL to the student visa policy page
        metadata: Source metadata including:
            - country: "DE"
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
        result.metadata['source'] = 'Germany DAAD'
        result.metadata['visa_category'] = 'Student'
        result.metadata['route'] = 'India → Germany'
        logger.info(f"Successfully fetched student visa content from DAAD {url} ({len(result.raw_text)} chars)")
    else:
        logger.error(f"Failed to fetch student visa content from DAAD {url}: {result.error_message}")
    
    return result

