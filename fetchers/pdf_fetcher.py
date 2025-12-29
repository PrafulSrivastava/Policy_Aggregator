"""PDF fetcher utilities for extracting text from PDF documents."""

import logging
import tempfile
import re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError, WrongPasswordError
from fetchers.base import FetchResult, FetchErrorType
from fetchers.html_fetcher import fetch_html_with_retry, DEFAULT_USER_AGENT, TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text content from a PDF file while preserving structure.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Extracted text with preserved paragraph structure
    
    Raises:
        PdfReadError: If PDF cannot be read
        WrongPasswordError: If PDF is encrypted
    """
    text_pages = []
    
    with open(pdf_path, 'rb') as pdf_file:
        reader = PdfReader(pdf_file)
        
        # Extract text from each page
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {e}")
                continue
    
    # Combine pages with double newline separator
    combined_text = '\n\n'.join(text_pages)
    
    # Normalize whitespace: multiple spaces to single space
    # But preserve line breaks and paragraph breaks
    combined_text = re.sub(r'[ \t]+', ' ', combined_text)  # Multiple spaces/tabs to single space
    combined_text = re.sub(r'\n{3,}', '\n\n', combined_text)  # Multiple newlines to double newline
    
    return combined_text.strip()


def extract_metadata_from_pdf(pdf_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Dictionary with PDF metadata (page_count, creation_date, etc.)
    
    Raises:
        PdfReadError: If PDF cannot be read
        WrongPasswordError: If PDF is encrypted
    """
    metadata = {}
    
    with open(pdf_path, 'rb') as pdf_file:
        reader = PdfReader(pdf_file)
        
        # Extract page count
        metadata['page_count'] = len(reader.pages)
        
        # Extract document metadata if available
        if reader.metadata:
            pdf_metadata = reader.metadata
            
            # Creation date
            if '/CreationDate' in pdf_metadata:
                creation_date = pdf_metadata['/CreationDate']
                metadata['creation_date'] = str(creation_date)
            
            # Modification date
            if '/ModDate' in pdf_metadata:
                mod_date = pdf_metadata['/ModDate']
                metadata['modification_date'] = str(mod_date)
            
            # Author
            if '/Author' in pdf_metadata:
                metadata['author'] = str(pdf_metadata['/Author'])
            
            # Title
            if '/Title' in pdf_metadata:
                metadata['title'] = str(pdf_metadata['/Title'])
            
            # Subject
            if '/Subject' in pdf_metadata:
                metadata['subject'] = str(pdf_metadata['/Subject'])
    
    return metadata


def download_pdf_from_url(url: str, headers: Optional[Dict[str, str]] = None) -> Path:
    """
    Download PDF from URL to a temporary file.
    
    Args:
        url: URL to download PDF from
        headers: Optional HTTP headers
    
    Returns:
        Path to temporary PDF file
    
    Raises:
        requests.RequestException: If download fails
    """
    if headers is None:
        headers = {}
    
    if 'User-Agent' not in headers:
        headers['User-Agent'] = DEFAULT_USER_AGENT
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_path = Path(temp_file.name)
    
    try:
        # Download PDF with retry logic
        response = fetch_html_with_retry(url, headers=headers, timeout=TIMEOUT_SECONDS)
        
        # Verify content type is PDF
        content_type = response.headers.get('Content-Type', '').lower()
        if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
            logger.warning(f"URL {url} may not be a PDF (Content-Type: {content_type})")
        
        # Write PDF content to temporary file
        temp_file.write(response.content)
        temp_file.close()
        
        return temp_path
        
    except Exception as e:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise


def fetch_pdf_from_file(file_path: str, metadata: Dict[str, Any]) -> FetchResult:
    """
    Extract text from a local PDF file.
    
    Args:
        file_path: Path to local PDF file
        metadata: Source metadata
    
    Returns:
        FetchResult with extracted text or error information
    """
    pdf_path = Path(file_path)
    
    if not pdf_path.exists():
        return FetchResult(
            raw_text="",
            content_type="pdf",
            success=False,
            error_message=f"{FetchErrorType.NOT_FOUND_ERROR.value}: PDF file not found: {file_path}"
        )
    
    try:
        # Extract text
        raw_text = extract_text_from_pdf(pdf_path)
        
        if not raw_text:
            logger.warning(f"No text extracted from PDF: {file_path}")
        
        # Extract metadata
        pdf_metadata = extract_metadata_from_pdf(pdf_path)
        
        # Merge with provided metadata
        pdf_metadata.update(metadata)
        
        return FetchResult(
            raw_text=raw_text,
            content_type="pdf",
            metadata=pdf_metadata,
            success=True
        )
        
    except WrongPasswordError as e:
        logger.error(f"PDF is encrypted: {file_path}")
        return FetchResult(
            raw_text="",
            content_type="pdf",
            success=False,
            error_message=f"{FetchErrorType.AUTHENTICATION_ERROR.value}: PDF is encrypted/protected and cannot be extracted"
        )
    
    except PdfReadError as e:
        logger.error(f"PDF read error: {file_path} - {e}")
        return FetchResult(
            raw_text="",
            content_type="pdf",
            success=False,
            error_message=f"{FetchErrorType.PARSE_ERROR.value}: PDF is corrupted or invalid: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error processing PDF {file_path}: {e}", exc_info=True)
        return FetchResult(
            raw_text="",
            content_type="pdf",
            success=False,
            error_message=f"{FetchErrorType.UNKNOWN_ERROR.value}: {str(e)}"
        )


def fetch_pdf(url: str, metadata: Dict[str, Any]) -> FetchResult:
    """
    Fetch PDF content from a URL and extract text.
    
    Downloads PDF to temporary file, extracts text, then cleans up.
    
    Args:
        url: URL to PDF file
        metadata: Source metadata (country, visa_type, etc.)
    
    Returns:
        FetchResult with extracted text or error information
    """
    # Check if this is a local file path (for testing)
    if 'file_path' in metadata:
        return fetch_pdf_from_file(metadata['file_path'], metadata)
    
    temp_pdf_path = None
    
    try:
        # Download PDF to temporary file
        user_agent = metadata.get('user_agent', DEFAULT_USER_AGENT)
        headers = {'User-Agent': user_agent}
        
        temp_pdf_path = download_pdf_from_url(url, headers=headers)
        
        # Extract text from PDF
        raw_text = extract_text_from_pdf(temp_pdf_path)
        
        if not raw_text:
            logger.warning(f"No text extracted from PDF: {url}")
        
        # Extract metadata
        pdf_metadata = extract_metadata_from_pdf(temp_pdf_path)
        
        # Add download metadata
        pdf_metadata['source_url'] = url
        pdf_metadata['downloaded_at'] = datetime.utcnow().isoformat()
        
        # Merge with provided metadata
        pdf_metadata.update(metadata)
        
        return FetchResult(
            raw_text=raw_text,
            content_type="pdf",
            metadata=pdf_metadata,
            success=True
        )
        
    except requests.exceptions.Timeout:
        return FetchResult(
            raw_text="",
            content_type="pdf",
            success=False,
            error_message=f"{FetchErrorType.TIMEOUT_ERROR.value}: Request timed out after {TIMEOUT_SECONDS}s"
        )
    
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else None
        error_type = FetchErrorType.NOT_FOUND_ERROR if status_code == 404 else FetchErrorType.NETWORK_ERROR
        return FetchResult(
            raw_text="",
            content_type="pdf",
            success=False,
            error_message=f"{error_type.value}: HTTP {status_code} - {str(e)}"
        )
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error downloading PDF {url}: {e}", exc_info=True)
        return FetchResult(
            raw_text="",
            content_type="pdf",
            success=False,
            error_message=f"{FetchErrorType.NETWORK_ERROR.value}: {str(e)}"
        )
    
    except WrongPasswordError as e:
        logger.error(f"PDF is encrypted: {url}")
        return FetchResult(
            raw_text="",
            content_type="pdf",
            success=False,
            error_message=f"{FetchErrorType.AUTHENTICATION_ERROR.value}: PDF is encrypted/protected and cannot be extracted"
        )
    
    except PdfReadError as e:
        logger.error(f"PDF read error: {url} - {e}")
        return FetchResult(
            raw_text="",
            content_type="pdf",
            success=False,
            error_message=f"{FetchErrorType.PARSE_ERROR.value}: PDF is corrupted or invalid: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error processing PDF {url}: {e}", exc_info=True)
        return FetchResult(
            raw_text="",
            content_type="pdf",
            success=False,
            error_message=f"{FetchErrorType.UNKNOWN_ERROR.value}: {str(e)}"
        )
    
    finally:
        # Always clean up temporary file
        if temp_pdf_path and temp_pdf_path.exists():
            try:
                temp_pdf_path.unlink()
                logger.debug(f"Cleaned up temporary PDF file: {temp_pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary PDF file {temp_pdf_path}: {e}")

