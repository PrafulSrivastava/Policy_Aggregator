"""
Example fetcher template for creating new source fetchers.

This file demonstrates the structure and requirements for creating a new fetcher plugin.
Copy this file and rename it following the convention: {country}_{agency}_{visa_type}.py

Example: de_bmi_workvisa.py for Germany BMI Work visa fetcher
"""

import logging
from typing import Dict, Any
from fetchers.base import FetchResult, FetchErrorType

logger = logging.getLogger(__name__)

# Optional: Specify the source type this fetcher handles
# This helps the fetcher manager match sources to fetchers
SOURCE_TYPE = "html"  # Options: "html", "pdf", "api"


def fetch(url: str, metadata: Dict[str, Any]) -> FetchResult:
    """
    Fetch content from a source URL.
    
    This is the standard interface that all fetchers must implement.
    
    Args:
        url: The URL to fetch content from
        metadata: Additional metadata about the source, including:
            - country: ISO country code (e.g., "DE")
            - visa_type: Type of visa (e.g., "Work", "Student")
            - fetch_type: How to fetch ("html" or "pdf")
            - Any other source-specific configuration
    
    Returns:
        FetchResult containing:
            - raw_text: Extracted text content
            - content_type: "html", "pdf", or "text"
            - fetched_at: Timestamp of fetch
            - metadata: Additional fetch metadata
            - success: Whether fetch succeeded
            - error_message: Error message if failed
    
    Important:
        - DO NOT raise exceptions. Return FetchResult with success=False instead.
        - Always return a FetchResult, even on failure.
        - Include helpful error messages for debugging.
    """
    try:
        # TODO: Implement your fetcher logic here
        # Example for HTML fetching:
        # import requests
        # response = requests.get(url, timeout=30)
        # response.raise_for_status()
        # raw_text = extract_text_from_html(response.text)
        
        # Example for PDF fetching:
        # import requests
        # response = requests.get(url, timeout=30)
        # raw_text = extract_text_from_pdf(response.content)
        
        # For this template, return a placeholder
        return FetchResult(
            raw_text="",
            content_type=SOURCE_TYPE,
            success=False,
            error_message="Template fetcher not implemented"
        )
        
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error fetching from {url}: {e}", exc_info=True)
        
        # Return error result instead of raising exception
        return FetchResult(
            raw_text="",
            content_type=SOURCE_TYPE,
            success=False,
            error_message=f"{FetchErrorType.UNKNOWN_ERROR.value}: {str(e)}"
        )


# Example of a more complete implementation:
"""
import requests
from bs4 import BeautifulSoup
from fetchers.base import FetchResult, FetchErrorType

def fetch(url: str, metadata: Dict[str, Any]) -> FetchResult:
    try:
        # Fetch the HTML content
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; PolicyAggregator/1.0)'
        })
        response.raise_for_status()
        
        # Parse HTML and extract text
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        raw_text = soup.get_text(separator=' ', strip=True)
        
        # Extract additional metadata
        page_title = soup.title.string if soup.title else None
        fetch_metadata = {
            'page_title': page_title,
            'content_length': len(raw_text),
            'status_code': response.status_code
        }
        
        return FetchResult(
            raw_text=raw_text,
            content_type="html",
            metadata=fetch_metadata,
            success=True
        )
        
    except requests.exceptions.Timeout:
        return FetchResult(
            raw_text="",
            content_type="html",
            success=False,
            error_message=f"{FetchErrorType.TIMEOUT_ERROR.value}: Request timed out"
        )
    except requests.exceptions.RequestException as e:
        return FetchResult(
            raw_text="",
            content_type="html",
            success=False,
            error_message=f"{FetchErrorType.NETWORK_ERROR.value}: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
        return FetchResult(
            raw_text="",
            content_type="html",
            success=False,
            error_message=f"{FetchErrorType.UNKNOWN_ERROR.value}: {str(e)}"
        )
"""



