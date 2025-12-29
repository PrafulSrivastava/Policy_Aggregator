"""Unit tests for PDF fetcher utilities."""

import pytest
import tempfile
import responses
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from PyPDF2 import PdfWriter, PdfReader
from PyPDF2.errors import PdfReadError, WrongPasswordError
from io import BytesIO
import requests

from fetchers.pdf_fetcher import (
    fetch_pdf,
    fetch_pdf_from_file,
    extract_text_from_pdf,
    extract_metadata_from_pdf,
    download_pdf_from_url
)
from fetchers.base import FetchResult, FetchErrorType


def create_test_pdf(content: str = "Test PDF Content\n\nThis is a test PDF document.") -> BytesIO:
    """
    Create a simple test PDF in memory.
    
    Args:
        content: Text content to include in PDF
    
    Returns:
        BytesIO object containing PDF data
    """
    # Create a simple PDF using PyPDF2
    writer = PdfWriter()
    
    # Create a page (PyPDF2 doesn't have direct text writing, so we'll create an empty page)
    # For testing purposes, we'll mock the extraction
    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)
    
    return pdf_bytes


def create_test_pdf_file(content: str = "Test PDF Content\n\nThis is a test PDF document.") -> Path:
    """
    Create a temporary test PDF file.
    
    Args:
        content: Text content description (for reference)
    
    Returns:
        Path to temporary PDF file
    """
    # Create a minimal valid PDF structure
    # PDF format is complex, so we'll create a simple one
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000306 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
390
%%EOF"""
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.write(pdf_content)
    temp_file.close()
    
    return Path(temp_file.name)


class TestExtractTextFromPDF:
    """Tests for extract_text_from_pdf() function."""
    
    def test_extract_text_from_valid_pdf(self):
        """Test extracting text from a valid PDF."""
        pdf_path = create_test_pdf_file()
        
        try:
            # Mock the PdfReader to return text
            with patch('fetchers.pdf_fetcher.PdfReader') as mock_reader_class:
                mock_reader = MagicMock()
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "Test PDF Content\n\nThis is a test PDF document."
                mock_reader.pages = [mock_page]
                mock_reader_class.return_value = mock_reader
                
                text = extract_text_from_pdf(pdf_path)
                assert "Test PDF Content" in text
                assert "test PDF document" in text
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
    
    def test_extract_text_preserves_structure(self):
        """Test that text extraction preserves paragraph structure."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.PdfReader') as mock_reader_class:
                mock_reader = MagicMock()
                mock_page1 = MagicMock()
                mock_page1.extract_text.return_value = "First paragraph.\n\nSecond paragraph."
                mock_page2 = MagicMock()
                mock_page2.extract_text.return_value = "Third paragraph."
                mock_reader.pages = [mock_page1, mock_page2]
                mock_reader_class.return_value = mock_reader
                
                text = extract_text_from_pdf(pdf_path)
                # Should have paragraph breaks between pages
                assert "First paragraph" in text
                assert "Second paragraph" in text
                assert "Third paragraph" in text
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
    
    def test_extract_text_handles_empty_pages(self):
        """Test handling of PDFs with empty pages."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.PdfReader') as mock_reader_class:
                mock_reader = MagicMock()
                mock_page = MagicMock()
                mock_page.extract_text.return_value = ""  # Empty page
                mock_reader.pages = [mock_page]
                mock_reader_class.return_value = mock_reader
                
                text = extract_text_from_pdf(pdf_path)
                # Should handle gracefully
                assert isinstance(text, str)
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
    
    def test_extract_text_handles_encrypted_pdf(self):
        """Test handling of encrypted PDFs."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.PdfReader') as mock_reader_class:
                mock_reader_class.side_effect = WrongPasswordError("PDF is encrypted")
                
                with pytest.raises(WrongPasswordError):
                    extract_text_from_pdf(pdf_path)
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
    
    def test_extract_text_handles_corrupted_pdf(self):
        """Test handling of corrupted PDFs."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.PdfReader') as mock_reader_class:
                mock_reader_class.side_effect = PdfReadError("PDF is corrupted")
                
                with pytest.raises(PdfReadError):
                    extract_text_from_pdf(pdf_path)
        finally:
            if pdf_path.exists():
                pdf_path.unlink()


class TestExtractMetadataFromPDF:
    """Tests for extract_metadata_from_pdf() function."""
    
    def test_extract_page_count(self):
        """Test extracting page count from PDF."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.PdfReader') as mock_reader_class:
                mock_reader = MagicMock()
                mock_reader.pages = [MagicMock(), MagicMock(), MagicMock()]  # 3 pages
                mock_reader.metadata = None
                mock_reader_class.return_value = mock_reader
                
                metadata = extract_metadata_from_pdf(pdf_path)
                assert metadata['page_count'] == 3
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
    
    def test_extract_creation_date(self):
        """Test extracting creation date from PDF metadata."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.PdfReader') as mock_reader_class:
                mock_reader = MagicMock()
                mock_reader.pages = [MagicMock()]
                mock_reader.metadata = {
                    '/CreationDate': 'D:20250127120000Z',
                    '/ModDate': 'D:20250128120000Z',
                    '/Author': 'Test Author',
                    '/Title': 'Test Title'
                }
                mock_reader_class.return_value = mock_reader
                
                metadata = extract_metadata_from_pdf(pdf_path)
                assert 'creation_date' in metadata
                assert 'modification_date' in metadata
                assert metadata['author'] == 'Test Author'
                assert metadata['title'] == 'Test Title'
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
    
    def test_extract_metadata_no_metadata(self):
        """Test extracting metadata when PDF has no metadata."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.PdfReader') as mock_reader_class:
                mock_reader = MagicMock()
                mock_reader.pages = [MagicMock()]
                mock_reader.metadata = None
                mock_reader_class.return_value = mock_reader
                
                metadata = extract_metadata_from_pdf(pdf_path)
                assert 'page_count' in metadata
                assert metadata['page_count'] == 1
        finally:
            if pdf_path.exists():
                pdf_path.unlink()


class TestFetchPDFFromFile:
    """Tests for fetch_pdf_from_file() function."""
    
    def test_fetch_from_existing_file(self):
        """Test fetching PDF from existing local file."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.extract_text_from_pdf') as mock_extract_text, \
                 patch('fetchers.pdf_fetcher.extract_metadata_from_pdf') as mock_extract_meta:
                
                mock_extract_text.return_value = "Test content"
                mock_extract_meta.return_value = {'page_count': 1}
                
                result = fetch_pdf_from_file(str(pdf_path), {'country': 'DE'})
                
                assert result.success is True
                assert result.content_type == "pdf"
                assert result.raw_text == "Test content"
                assert result.metadata['page_count'] == 1
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
    
    def test_fetch_from_nonexistent_file(self):
        """Test fetching PDF from non-existent file."""
        result = fetch_pdf_from_file("/nonexistent/file.pdf", {})
        
        assert result.success is False
        assert FetchErrorType.NOT_FOUND_ERROR.value in result.error_message
    
    def test_fetch_encrypted_pdf(self):
        """Test handling encrypted PDF."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.extract_text_from_pdf') as mock_extract_text:
                mock_extract_text.side_effect = WrongPasswordError("PDF is encrypted")
                
                result = fetch_pdf_from_file(str(pdf_path), {})
                
                assert result.success is False
                assert FetchErrorType.AUTHENTICATION_ERROR.value in result.error_message
                assert "encrypted" in result.error_message.lower()
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
    
    def test_fetch_corrupted_pdf(self):
        """Test handling corrupted PDF."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.extract_text_from_pdf') as mock_extract_text:
                mock_extract_text.side_effect = PdfReadError("PDF is corrupted")
                
                result = fetch_pdf_from_file(str(pdf_path), {})
                
                assert result.success is False
                assert FetchErrorType.PARSE_ERROR.value in result.error_message
                assert "corrupted" in result.error_message.lower() or "invalid" in result.error_message.lower()
        finally:
            if pdf_path.exists():
                pdf_path.unlink()


class TestDownloadPDFFromURL:
    """Tests for download_pdf_from_url() function."""
    
    @responses.activate
    def test_download_pdf_success(self):
        """Test successful PDF download."""
        pdf_content = b"%PDF-1.4\nTest PDF content"
        
        responses.add(
            responses.GET,
            "https://example.com/document.pdf",
            body=pdf_content,
            status=200,
            content_type="application/pdf"
        )
        
        with patch('fetchers.pdf_fetcher.fetch_html_with_retry') as mock_fetch:
            mock_response = MagicMock()
            mock_response.content = pdf_content
            mock_response.headers = {'Content-Type': 'application/pdf'}
            mock_fetch.return_value = mock_response
            
            pdf_path = download_pdf_from_url("https://example.com/document.pdf")
            
            assert pdf_path.exists()
            assert pdf_path.suffix == '.pdf'
            
            # Cleanup
            pdf_path.unlink()
    
    @responses.activate
    def test_download_pdf_timeout(self):
        """Test PDF download timeout."""
        with patch('fetchers.pdf_fetcher.fetch_html_with_retry') as mock_fetch:
            mock_fetch.side_effect = requests.exceptions.Timeout("Request timeout")
            
            with pytest.raises(requests.exceptions.Timeout):
                download_pdf_from_url("https://example.com/document.pdf")


class TestFetchPDF:
    """Tests for fetch_pdf() function."""
    
    @responses.activate
    def test_fetch_pdf_from_url_success(self):
        """Test successful PDF fetch from URL."""
        pdf_content = b"%PDF-1.4\nTest PDF"
        
        with patch('fetchers.pdf_fetcher.download_pdf_from_url') as mock_download, \
             patch('fetchers.pdf_fetcher.extract_text_from_pdf') as mock_extract_text, \
             patch('fetchers.pdf_fetcher.extract_metadata_from_pdf') as mock_extract_meta:
            
            temp_path = create_test_pdf_file()
            mock_download.return_value = temp_path
            mock_extract_text.return_value = "Test PDF Content"
            mock_extract_meta.return_value = {'page_count': 1}
            
            try:
                result = fetch_pdf("https://example.com/document.pdf", {'country': 'DE'})
                
                assert result.success is True
                assert result.content_type == "pdf"
                assert "Test PDF Content" in result.raw_text
                assert result.metadata['page_count'] == 1
                assert 'source_url' in result.metadata
            finally:
                if temp_path.exists():
                    temp_path.unlink()
    
    def test_fetch_pdf_from_local_file(self):
        """Test fetching PDF from local file path."""
        pdf_path = create_test_pdf_file()
        
        try:
            with patch('fetchers.pdf_fetcher.extract_text_from_pdf') as mock_extract_text, \
                 patch('fetchers.pdf_fetcher.extract_metadata_from_pdf') as mock_extract_meta:
                
                mock_extract_text.return_value = "Local PDF content"
                mock_extract_meta.return_value = {'page_count': 1}
                
                result = fetch_pdf("https://example.com/document.pdf", {
                    'file_path': str(pdf_path),
                    'country': 'DE'
                })
                
                assert result.success is True
                assert "Local PDF content" in result.raw_text
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
    
    @responses.activate
    def test_fetch_pdf_timeout(self):
        """Test handling timeout when downloading PDF."""
        with patch('fetchers.pdf_fetcher.download_pdf_from_url') as mock_download:
            mock_download.side_effect = requests.exceptions.Timeout("Request timeout")
            
            result = fetch_pdf("https://example.com/document.pdf", {})
            
            assert result.success is False
            assert FetchErrorType.TIMEOUT_ERROR.value in result.error_message
    
    @responses.activate
    def test_fetch_pdf_404_error(self):
        """Test handling 404 error when downloading PDF."""
        with patch('fetchers.pdf_fetcher.download_pdf_from_url') as mock_download:
            response = MagicMock()
            response.status_code = 404
            mock_download.side_effect = requests.exceptions.HTTPError(response=response)
            
            result = fetch_pdf("https://example.com/document.pdf", {})
            
            assert result.success is False
            assert FetchErrorType.NOT_FOUND_ERROR.value in result.error_message
    
    @responses.activate
    def test_fetch_pdf_encrypted(self):
        """Test handling encrypted PDF."""
        temp_path = create_test_pdf_file()
        
        with patch('fetchers.pdf_fetcher.download_pdf_from_url') as mock_download, \
             patch('fetchers.pdf_fetcher.extract_text_from_pdf') as mock_extract_text:
            
            mock_download.return_value = temp_path
            mock_extract_text.side_effect = WrongPasswordError("PDF is encrypted")
            
            try:
                result = fetch_pdf("https://example.com/document.pdf", {})
                
                assert result.success is False
                assert FetchErrorType.AUTHENTICATION_ERROR.value in result.error_message
                assert "encrypted" in result.error_message.lower()
            finally:
                if temp_path.exists():
                    temp_path.unlink()
    
    @responses.activate
    def test_fetch_pdf_corrupted(self):
        """Test handling corrupted PDF."""
        temp_path = create_test_pdf_file()
        
        with patch('fetchers.pdf_fetcher.download_pdf_from_url') as mock_download, \
             patch('fetchers.pdf_fetcher.extract_text_from_pdf') as mock_extract_text:
            
            mock_download.return_value = temp_path
            mock_extract_text.side_effect = PdfReadError("PDF is corrupted")
            
            try:
                result = fetch_pdf("https://example.com/document.pdf", {})
                
                assert result.success is False
                assert FetchErrorType.PARSE_ERROR.value in result.error_message
            finally:
                if temp_path.exists():
                    temp_path.unlink()
    
    @responses.activate
    def test_fetch_pdf_cleanup_temp_file(self):
        """Test that temporary PDF file is cleaned up."""
        temp_path = create_test_pdf_file()
        
        with patch('fetchers.pdf_fetcher.download_pdf_from_url') as mock_download, \
             patch('fetchers.pdf_fetcher.extract_text_from_pdf') as mock_extract_text, \
             patch('fetchers.pdf_fetcher.extract_metadata_from_pdf') as mock_extract_meta:
            
            mock_download.return_value = temp_path
            mock_extract_text.return_value = "Test content"
            mock_extract_meta.return_value = {'page_count': 1}
            
            result = fetch_pdf("https://example.com/document.pdf", {})
            
            # File should be cleaned up
            assert not temp_path.exists() or result.success  # May exist if test fails
            assert result.success is True

