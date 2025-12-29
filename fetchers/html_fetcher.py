"""HTML fetcher utilities for fetching and parsing HTML content from web pages."""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from fetchers.base import FetchResult, FetchErrorType

logger = logging.getLogger(__name__)

# Default User-Agent header
DEFAULT_USER_AGENT = "PolicyAggregator/1.0 (compatible; +https://github.com/policy-aggregator)"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1  # Base delay in seconds for exponential backoff
RETRY_STATUS_CODES = {500, 502, 503, 504}  # Transient server errors
TIMEOUT_SECONDS = 30
MAX_REDIRECTS = 5


def check_robots_txt(url: str, user_agent: str = DEFAULT_USER_AGENT) -> Tuple[bool, Optional[str]]:
    """
    Check if URL is allowed by robots.txt.
    
    Args:
        url: The URL to check
        user_agent: User agent string to check against robots.txt
    
    Returns:
        Tuple of (is_allowed, error_message)
        - is_allowed: True if allowed, False if blocked
        - error_message: Error message if robots.txt check failed (None if successful)
    """
    try:
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        is_allowed = rp.can_fetch(user_agent, url)
        
        if not is_allowed:
            logger.warning(f"URL blocked by robots.txt: {url}")
            return False, f"URL blocked by robots.txt for user agent: {user_agent}"
        
        return True, None
        
    except Exception as e:
        # If robots.txt is unavailable or unparseable, proceed with fetch
        # This is a common pattern - many sites don't have robots.txt
        logger.debug(f"Could not check robots.txt for {url}: {e}. Proceeding with fetch.")
        return True, None


def fetch_html_with_retry(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = TIMEOUT_SECONDS,
    max_retries: int = MAX_RETRIES
) -> requests.Response:
    """
    Fetch HTML content with retry logic for transient failures.
    
    Args:
        url: URL to fetch
        headers: Optional HTTP headers
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    
    Returns:
        requests.Response object
    
    Raises:
        requests.RequestException: If all retries fail
    """
    if headers is None:
        headers = {}
    
    if 'User-Agent' not in headers:
        headers['User-Agent'] = DEFAULT_USER_AGENT
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True
            )
            
            # Check if status code indicates transient failure
            if response.status_code in RETRY_STATUS_CODES and attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    f"Transient error {response.status_code} for {url}, "
                    f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                continue
            
            # For non-transient errors, raise immediately
            # Check for 404 before raising to preserve status code
            if response.status_code == 404:
                raise requests.exceptions.HTTPError(f"404 Client Error: Not Found for url: {url}", response=response)
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(f"Timeout for {url}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise
        
        except requests.exceptions.RequestException as e:
            # For non-retryable errors (4xx except some), raise immediately
            if hasattr(e.response, 'status_code') and e.response.status_code not in RETRY_STATUS_CODES:
                raise
            
            last_exception = e
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(f"Request error for {url}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise
    
    # If we get here, all retries failed
    raise last_exception


def extract_text_from_html(html_content: str) -> str:
    """
    Extract clean text content from HTML.
    
    Tries to extract from semantic HTML elements in order:
    1. <main> tag
    2. <article> tag
    3. <div> containers with common content classes
    4. Fallback to <body>
    
    Args:
        html_content: Raw HTML content
    
    Returns:
        Clean text content with preserved structure
    """
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        element.decompose()
    
    # Try to find main content area
    content_element = None
    
    # 1. Try <main> tag
    if soup.find('main'):
        content_element = soup.find('main')
    # 2. Try <article> tag
    elif soup.find('article'):
        content_element = soup.find('article')
    # 3. Try common content div classes
    elif soup.find('div', class_=lambda x: x and any(
        class_name in ' '.join(x).lower() 
        for class_name in ['content', 'main', 'article', 'post', 'entry', 'body']
    )):
        content_element = soup.find('div', class_=lambda x: x and any(
            class_name in ' '.join(x).lower() 
            for class_name in ['content', 'main', 'article', 'post', 'entry', 'body']
        ))
    # 4. Fallback to <body>
    elif soup.find('body'):
        content_element = soup.find('body')
    else:
        # Last resort: entire document
        content_element = soup
    
    if content_element:
        # Get text with preserved line breaks
        text = content_element.get_text(separator='\n', strip=True)
        # Normalize multiple newlines to double newline (paragraph break)
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    return ""


def extract_metadata_from_html(soup: BeautifulSoup, response: requests.Response) -> Dict[str, Any]:
    """
    Extract metadata from HTML and HTTP response.
    
    Args:
        soup: BeautifulSoup parsed HTML
        response: requests.Response object
    
    Returns:
        Dictionary with metadata (title, last_modified, etc.)
    """
    metadata = {}
    
    # Extract page title
    if soup.title and soup.title.string:
        metadata['page_title'] = soup.title.string.strip()
    
    # Extract last modified date from various sources
    last_modified = None
    
    # 1. Check HTTP Last-Modified header
    if 'Last-Modified' in response.headers:
        last_modified = response.headers['Last-Modified']
        metadata['last_modified_header'] = last_modified
    
    # 2. Check meta tag
    meta_lastmod = soup.find('meta', attrs={'name': 'last-modified'}) or \
                   soup.find('meta', attrs={'property': 'article:modified_time'}) or \
                   soup.find('meta', attrs={'name': 'date'})
    
    if meta_lastmod:
        content = meta_lastmod.get('content') or meta_lastmod.get('value')
        if content:
            last_modified = content
            metadata['last_modified_meta'] = content
    
    if last_modified:
        metadata['last_modified'] = last_modified
    
    # Extract other useful metadata
    if response.url != response.request.url:
        metadata['final_url'] = response.url
        metadata['redirected'] = True
    
    metadata['status_code'] = response.status_code
    metadata['content_length'] = len(response.content)
    
    # Extract description if available
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        metadata['description'] = meta_desc.get('content')
    
    return metadata


def fetch_html(url: str, metadata: Dict[str, Any]) -> FetchResult:
    """
    Fetch HTML content from a URL with full error handling and retry logic.
    
    This is a utility function that can be used by individual fetchers.
    It handles:
    - robots.txt checking
    - HTTP requests with retry logic
    - HTML parsing and text extraction
    - Metadata extraction
    - Error handling
    
    Args:
        url: URL to fetch
        metadata: Source metadata (country, visa_type, etc.)
    
    Returns:
        FetchResult with fetched content or error information
    """
    try:
        # Check robots.txt
        user_agent = metadata.get('user_agent', DEFAULT_USER_AGENT)
        is_allowed, robots_error = check_robots_txt(url, user_agent)
        
        if not is_allowed:
            return FetchResult(
                raw_text="",
                content_type="html",
                success=False,
                error_message=f"{FetchErrorType.NETWORK_ERROR.value}: {robots_error}"
            )
        
        # Fetch HTML with retry logic
        headers = {
            'User-Agent': user_agent
        }
        
        response = fetch_html_with_retry(url, headers=headers)
        
        # Parse HTML and extract text
        raw_text = extract_text_from_html(response.text)
        
        if not raw_text:
            logger.warning(f"No text content extracted from {url}")
        
        # Extract metadata
        soup = BeautifulSoup(response.text, 'lxml')
        fetch_metadata = extract_metadata_from_html(soup, response)
        
        # Merge with provided metadata
        fetch_metadata.update(metadata)
        
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
            error_message=f"{FetchErrorType.TIMEOUT_ERROR.value}: Request timed out after {TIMEOUT_SECONDS}s"
        )
    
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else None
        # Check error message for 404 if status_code is not available
        if status_code is None and ("404" in str(e) or "Not Found" in str(e)):
            status_code = 404
        error_type = FetchErrorType.NOT_FOUND_ERROR if status_code == 404 else FetchErrorType.NETWORK_ERROR
        return FetchResult(
            raw_text="",
            content_type="html",
            success=False,
            error_message=f"{error_type.value}: HTTP {status_code} - {str(e)}"
        )
    
    except requests.exceptions.RequestException as e:
        # Check if it's a 404 error from the error message
        error_str = str(e)
        if "404" in error_str or "Not Found" in error_str:
            return FetchResult(
                raw_text="",
                content_type="html",
                success=False,
                error_message=f"{FetchErrorType.NOT_FOUND_ERROR.value}: {error_str}"
            )
        logger.error(f"Network error fetching {url}: {e}", exc_info=True)
        return FetchResult(
            raw_text="",
            content_type="html",
            success=False,
            error_message=f"{FetchErrorType.NETWORK_ERROR.value}: {error_str}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
        return FetchResult(
            raw_text="",
            content_type="html",
            success=False,
            error_message=f"{FetchErrorType.UNKNOWN_ERROR.value}: {str(e)}"
        )

