"""Unit tests for HTML fetcher utilities."""

import pytest
import responses
from unittest.mock import patch, MagicMock
from requests.exceptions import Timeout, HTTPError, RequestException
from fetchers.html_fetcher import (
    fetch_html,
    fetch_html_with_retry,
    extract_text_from_html,
    extract_metadata_from_html,
    check_robots_txt,
    DEFAULT_USER_AGENT,
    MAX_RETRIES,
    RETRY_STATUS_CODES
)
from fetchers.base import FetchResult, FetchErrorType
from bs4 import BeautifulSoup
import requests


class TestExtractTextFromHTML:
    """Tests for extract_text_from_html() function."""
    
    def test_extract_from_main_tag(self):
        """Test extracting text from <main> tag."""
        html = """
        <html>
            <body>
                <nav>Navigation</nav>
                <main>
                    <h1>Main Content</h1>
                    <p>This is the main content area.</p>
                </main>
                <footer>Footer</footer>
            </body>
        </html>
        """
        text = extract_text_from_html(html)
        assert "Main Content" in text
        assert "This is the main content area" in text
        assert "Navigation" not in text
        assert "Footer" not in text
    
    def test_extract_from_article_tag(self):
        """Test extracting text from <article> tag when no <main>."""
        html = """
        <html>
            <body>
                <article>
                    <h1>Article Title</h1>
                    <p>Article content here.</p>
                </article>
            </body>
        </html>
        """
        text = extract_text_from_html(html)
        assert "Article Title" in text
        assert "Article content here" in text
    
    def test_extract_from_content_div(self):
        """Test extracting text from content div when no semantic tags."""
        html = """
        <html>
            <body>
                <div class="main-content">
                    <h1>Content Title</h1>
                    <p>Content here.</p>
                </div>
            </body>
        </html>
        """
        text = extract_text_from_html(html)
        assert "Content Title" in text
        assert "Content here" in text
    
    def test_fallback_to_body(self):
        """Test fallback to <body> when no content areas found."""
        html = """
        <html>
            <body>
                <h1>Body Content</h1>
                <p>Body text here.</p>
            </body>
        </html>
        """
        text = extract_text_from_html(html)
        assert "Body Content" in text
        assert "Body text here" in text
    
    def test_removes_script_and_style(self):
        """Test that script and style elements are removed."""
        html = """
        <html>
            <body>
                <script>alert('test');</script>
                <style>.hidden { display: none; }</style>
                <p>Visible content</p>
            </body>
        </html>
        """
        text = extract_text_from_html(html)
        assert "alert" not in text
        assert "hidden" not in text
        assert "Visible content" in text
    
    def test_preserves_structure(self):
        """Test that basic structure (paragraphs, line breaks) is preserved."""
        html = """
        <html>
            <body>
                <p>First paragraph</p>
                <p>Second paragraph</p>
            </body>
        </html>
        """
        text = extract_text_from_html(html)
        # Should have some separation between paragraphs
        assert "First paragraph" in text
        assert "Second paragraph" in text


class TestExtractMetadataFromHTML:
    """Tests for extract_metadata_from_html() function."""
    
    def test_extract_page_title(self):
        """Test extracting page title."""
        html = "<html><head><title>Test Page Title</title></head><body></body></html>"
        soup = BeautifulSoup(html, 'lxml')
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.url = "https://example.com"
        mock_response.request.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.content = b"test"
        
        metadata = extract_metadata_from_html(soup, mock_response)
        assert metadata['page_title'] == "Test Page Title"
    
    def test_extract_last_modified_from_header(self):
        """Test extracting last modified from HTTP header."""
        html = "<html><head></head><body></body></html>"
        soup = BeautifulSoup(html, 'lxml')
        mock_response = MagicMock()
        mock_response.headers = {'Last-Modified': 'Wed, 21 Oct 2015 07:28:00 GMT'}
        mock_response.url = "https://example.com"
        mock_response.request.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.content = b"test"
        
        metadata = extract_metadata_from_html(soup, mock_response)
        assert metadata['last_modified'] == 'Wed, 21 Oct 2015 07:28:00 GMT'
        assert metadata['last_modified_header'] == 'Wed, 21 Oct 2015 07:28:00 GMT'
    
    def test_extract_last_modified_from_meta_tag(self):
        """Test extracting last modified from meta tag."""
        html = """
        <html>
            <head>
                <meta name="last-modified" content="2025-01-27T10:00:00Z">
            </head>
            <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.url = "https://example.com"
        mock_response.request.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.content = b"test"
        
        metadata = extract_metadata_from_html(soup, mock_response)
        assert 'last_modified' in metadata
        assert '2025-01-27' in metadata['last_modified']
    
    def test_detect_redirect(self):
        """Test detecting redirects."""
        html = "<html><head></head><body></body></html>"
        soup = BeautifulSoup(html, 'lxml')
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.url = "https://example.com/final"
        mock_response.request.url = "https://example.com/original"
        mock_response.status_code = 200
        mock_response.content = b"test"
        
        metadata = extract_metadata_from_html(soup, mock_response)
        assert metadata['redirected'] is True
        assert metadata['final_url'] == "https://example.com/final"
    
    def test_extract_description(self):
        """Test extracting meta description."""
        html = """
        <html>
            <head>
                <meta name="description" content="Test description">
            </head>
            <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.url = "https://example.com"
        mock_response.request.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.content = b"test"
        
        metadata = extract_metadata_from_html(soup, mock_response)
        assert metadata['description'] == "Test description"


class TestCheckRobotsTxt:
    """Tests for check_robots_txt() function."""
    
    @patch('fetchers.html_fetcher.RobotFileParser')
    def test_allowed_by_robots_txt(self, mock_robot_parser):
        """Test when robots.txt allows the URL."""
        mock_rp = MagicMock()
        mock_rp.can_fetch.return_value = True
        mock_robot_parser.return_value = mock_rp
        
        is_allowed, error = check_robots_txt("https://example.com/page", "TestBot/1.0")
        assert is_allowed is True
        assert error is None
    
    @patch('fetchers.html_fetcher.RobotFileParser')
    def test_blocked_by_robots_txt(self, mock_robot_parser):
        """Test when robots.txt blocks the URL."""
        mock_rp = MagicMock()
        mock_rp.can_fetch.return_value = False
        mock_robot_parser.return_value = mock_rp
        
        is_allowed, error = check_robots_txt("https://example.com/page", "TestBot/1.0")
        assert is_allowed is False
        assert error is not None
        assert "blocked" in error.lower()
    
    @patch('fetchers.html_fetcher.RobotFileParser')
    def test_robots_txt_unavailable(self, mock_robot_parser):
        """Test when robots.txt is unavailable (should proceed)."""
        mock_robot_parser.side_effect = Exception("robots.txt not found")
        
        is_allowed, error = check_robots_txt("https://example.com/page", "TestBot/1.0")
        # Should proceed if robots.txt unavailable
        assert is_allowed is True
        assert error is None


class TestFetchHTMLWithRetry:
    """Tests for fetch_html_with_retry() function."""
    
    @responses.activate
    def test_successful_fetch(self):
        """Test successful fetch without retries."""
        responses.add(
            responses.GET,
            "https://example.com",
            body="<html><body>Test</body></html>",
            status=200
        )
        
        response = fetch_html_with_retry("https://example.com")
        assert response.status_code == 200
        assert "Test" in response.text
    
    @responses.activate
    def test_retry_on_transient_error(self):
        """Test retry logic on transient server errors."""
        # First attempt: 500 error
        responses.add(
            responses.GET,
            "https://example.com",
            status=500
        )
        # Second attempt: success
        responses.add(
            responses.GET,
            "https://example.com",
            body="<html><body>Success</body></html>",
            status=200
        )
        
        with patch('time.sleep'):  # Speed up test by mocking sleep
            response = fetch_html_with_retry("https://example.com", max_retries=2)
            assert response.status_code == 200
            assert len(responses.calls) == 2  # Should have retried
    
    @responses.activate
    def test_timeout_with_retry(self):
        """Test timeout handling with retry."""
        responses.add(
            responses.GET,
            "https://example.com",
            body=Timeout("Connection timeout")
        )
        responses.add(
            responses.GET,
            "https://example.com",
            body="<html><body>Success</body></html>",
            status=200
        )
        
        with patch('time.sleep'):
            response = fetch_html_with_retry("https://example.com", max_retries=2)
            assert response.status_code == 200
    
    @responses.activate
    def test_404_error_no_retry(self):
        """Test that 404 errors don't trigger retries."""
        responses.add(
            responses.GET,
            "https://example.com",
            status=404
        )
        
        with pytest.raises(HTTPError):
            fetch_html_with_retry("https://example.com")
        
        # Should not retry 404
        assert len(responses.calls) == 1


class TestFetchHTML:
    """Tests for fetch_html() function."""
    
    @responses.activate
    @patch('fetchers.html_fetcher.check_robots_txt')
    def test_successful_fetch(self, mock_check_robots):
        """Test successful HTML fetch."""
        mock_check_robots.return_value = (True, None)
        
        responses.add(
            responses.GET,
            "https://example.com",
            body="""
            <html>
                <head>
                    <title>Test Page</title>
                </head>
                <body>
                    <main>
                        <h1>Main Content</h1>
                        <p>Content here.</p>
                    </main>
                </body>
            </html>
            """,
            status=200,
            headers={'Last-Modified': 'Wed, 21 Oct 2015 07:28:00 GMT'}
        )
        
        result = fetch_html("https://example.com", {"country": "DE", "visa_type": "Student"})
        
        assert result.success is True
        assert result.content_type == "html"
        assert "Main Content" in result.raw_text
        assert "Content here" in result.raw_text
        assert result.metadata['page_title'] == "Test Page"
        assert 'last_modified' in result.metadata
    
    @responses.activate
    @patch('fetchers.html_fetcher.check_robots_txt')
    def test_blocked_by_robots_txt(self, mock_check_robots):
        """Test when blocked by robots.txt."""
        mock_check_robots.return_value = (False, "Blocked by robots.txt")
        
        result = fetch_html("https://example.com", {})
        
        assert result.success is False
        assert "blocked" in result.error_message.lower()
        assert result.error_message.startswith(FetchErrorType.NETWORK_ERROR.value)
    
    @responses.activate
    @patch('fetchers.html_fetcher.check_robots_txt')
    def test_404_error(self, mock_check_robots):
        """Test handling 404 Not Found error."""
        mock_check_robots.return_value = (True, None)
        
        responses.add(
            responses.GET,
            "https://example.com",
            status=404
        )
        
        result = fetch_html("https://example.com", {})
        
        assert result.success is False
        assert FetchErrorType.NOT_FOUND_ERROR.value in result.error_message
        assert "404" in result.error_message
    
    @responses.activate
    @patch('fetchers.html_fetcher.check_robots_txt')
    def test_timeout_error(self, mock_check_robots):
        """Test handling timeout error."""
        mock_check_robots.return_value = (True, None)
        
        responses.add(
            responses.GET,
            "https://example.com",
            body=Timeout("Request timeout")
        )
        
        result = fetch_html("https://example.com", {})
        
        assert result.success is False
        assert FetchErrorType.TIMEOUT_ERROR.value in result.error_message
    
    @responses.activate
    @patch('fetchers.html_fetcher.check_robots_txt')
    def test_500_error_with_retry(self, mock_check_robots):
        """Test handling 500 error with retry."""
        mock_check_robots.return_value = (True, None)
        
        # First attempt: 500 error
        responses.add(
            responses.GET,
            "https://example.com",
            status=500
        )
        # Second attempt: success
        responses.add(
            responses.GET,
            "https://example.com",
            body="<html><body>Success after retry</body></html>",
            status=200
        )
        
        with patch('time.sleep'):
            result = fetch_html("https://example.com", {})
            assert result.success is True
            assert "Success after retry" in result.raw_text
    
    @responses.activate
    @patch('fetchers.html_fetcher.check_robots_txt')
    def test_redirect_handling(self, mock_check_robots):
        """Test handling redirects."""
        mock_check_robots.return_value = (True, None)
        
        responses.add(
            responses.GET,
            "https://example.com/original",
            status=301,
            headers={'Location': 'https://example.com/final'}
        )
        responses.add(
            responses.GET,
            "https://example.com/final",
            body="<html><body>Final content</body></html>",
            status=200
        )
        
        result = fetch_html("https://example.com/original", {})
        
        assert result.success is True
        assert "Final content" in result.raw_text
    
    @responses.activate
    @patch('fetchers.html_fetcher.check_robots_txt')
    def test_user_agent_header(self, mock_check_robots):
        """Test that User-Agent header is set correctly."""
        mock_check_robots.return_value = (True, None)
        
        responses.add(
            responses.GET,
            "https://example.com",
            body="<html><body>Test</body></html>",
            status=200
        )
        
        result = fetch_html("https://example.com", {"user_agent": "CustomBot/1.0"})
        
        assert result.success is True
        # Verify the request was made with correct User-Agent
        assert len(responses.calls) == 1
        request_headers = responses.calls[0].request.headers
        assert request_headers.get('User-Agent') == "CustomBot/1.0"



