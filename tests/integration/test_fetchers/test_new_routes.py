"""Integration tests for UK and Canada source fetchers."""

import pytest
from fetchers.uk_home_office_student import fetch as fetch_uk_student, SOURCE_TYPE as UK_STUDENT_TYPE
from fetchers.uk_home_office_work import fetch as fetch_uk_work, SOURCE_TYPE as UK_WORK_TYPE
from fetchers.uk_home_office_immigration_rules import fetch as fetch_uk_rules, SOURCE_TYPE as UK_RULES_TYPE
from fetchers.ca_ircc_student import fetch as fetch_ca_student, SOURCE_TYPE as CA_STUDENT_TYPE
from fetchers.ca_ircc_work import fetch as fetch_ca_work, SOURCE_TYPE as CA_WORK_TYPE
from fetchers.ca_ircc_operational_bulletins import fetch as fetch_ca_bulletins, SOURCE_TYPE as CA_BULLETINS_TYPE
from fetchers.base import FetchResult


class TestNewRoutesSourceFetchers:
    """Integration tests for UK and Canada source fetchers."""
    
    @pytest.mark.parametrize("fetcher_func,url,country,visa_type,source_type", [
        (fetch_uk_student, "https://www.gov.uk/student-visa", "UK", "Student", UK_STUDENT_TYPE),
        (fetch_uk_work, "https://www.gov.uk/skilled-worker-visa", "UK", "Work", UK_WORK_TYPE),
        (fetch_uk_rules, "https://www.gov.uk/guidance/immigration-rules", "UK", "Both", UK_RULES_TYPE),
        (fetch_ca_student, "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit.html", "CA", "Student", CA_STUDENT_TYPE),
        (fetch_ca_work, "https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada.html", "CA", "Work", CA_WORK_TYPE),
        (fetch_ca_bulletins, "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals.html", "CA", "Both", CA_BULLETINS_TYPE),
    ])
    def test_fetcher_loads_and_executes(self, fetcher_func, url, country, visa_type, source_type):
        """Test that each fetcher loads and executes with real URL."""
        metadata = {
            "country": country,
            "visa_type": visa_type,
            "fetch_type": source_type
        }
        
        # Execute fetcher
        result = fetcher_func(url, metadata)
        
        # Verify FetchResult is returned
        assert isinstance(result, FetchResult)
        assert result.content_type == source_type
        
        # Note: We don't assert success=True because URLs may not be accessible in test environment
        # The important thing is that the fetcher executes without exceptions
        assert result.error_message is None or result.success is False
    
    def test_uk_student_fetcher_returns_result(self):
        """Test UK Home Office student fetcher returns FetchResult."""
        url = "https://www.gov.uk/student-visa"
        metadata = {
            "country": "UK",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        result = fetch_uk_student(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "UK Home Office"
            assert result.metadata["visa_category"] == "Student"
            assert result.metadata["route"] == "India → UK"
    
    def test_uk_work_fetcher_returns_result(self):
        """Test UK Home Office work fetcher returns FetchResult."""
        url = "https://www.gov.uk/skilled-worker-visa"
        metadata = {
            "country": "UK",
            "visa_type": "Work",
            "fetch_type": "html"
        }
        
        result = fetch_uk_work(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "UK Home Office"
            assert result.metadata["visa_category"] == "Work"
            assert result.metadata["visa_subtype"] == "Skilled Worker"
            assert result.metadata["route"] == "India → UK"
    
    def test_uk_immigration_rules_fetcher_returns_result(self):
        """Test UK Home Office immigration rules fetcher returns FetchResult."""
        url = "https://www.gov.uk/guidance/immigration-rules"
        metadata = {
            "country": "UK",
            "visa_type": "Both",
            "fetch_type": "html"
        }
        
        result = fetch_uk_rules(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "UK Home Office"
            assert result.metadata["content_scope"] == "Immigration Rules Guidance"
            assert result.metadata["route"] == "India → UK"
    
    def test_ca_student_fetcher_returns_result(self):
        """Test IRCC student fetcher returns FetchResult."""
        url = "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit.html"
        metadata = {
            "country": "CA",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        result = fetch_ca_student(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "IRCC"
            assert result.metadata["visa_category"] == "Student"
            assert result.metadata["visa_subtype"] == "Study Permit"
            assert result.metadata["route"] == "India → Canada"
    
    def test_ca_work_fetcher_returns_result(self):
        """Test IRCC work fetcher returns FetchResult."""
        url = "https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada.html"
        metadata = {
            "country": "CA",
            "visa_type": "Work",
            "fetch_type": "html"
        }
        
        result = fetch_ca_work(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "IRCC"
            assert result.metadata["visa_category"] == "Work"
            assert result.metadata["visa_subtype"] == "Work Permit"
            assert result.metadata["route"] == "India → Canada"
    
    def test_ca_operational_bulletins_fetcher_returns_result(self):
        """Test IRCC operational bulletins fetcher returns FetchResult."""
        url = "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals.html"
        metadata = {
            "country": "CA",
            "visa_type": "Both",
            "fetch_type": "html"
        }
        
        result = fetch_ca_bulletins(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "IRCC"
            assert result.metadata["content_scope"] == "Operational Bulletins and Manuals"
            assert result.metadata["route"] == "India → Canada"
    
    def test_all_fetchers_handle_errors_gracefully(self):
        """Test that all fetchers handle errors gracefully (no exceptions raised)."""
        invalid_url = "https://invalid-url-that-does-not-exist-12345.com/page"
        metadata = {
            "country": "UK",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        fetchers = [
            fetch_uk_student,
            fetch_uk_work,
            fetch_uk_rules,
            fetch_ca_student,
            fetch_ca_work,
            fetch_ca_bulletins
        ]
        
        for fetcher in fetchers:
            # Should not raise exception, should return FetchResult with success=False
            result = fetcher(invalid_url, metadata)
            assert isinstance(result, FetchResult)
            assert result.success is False
            assert result.error_message is not None
    
    def test_fetchers_extract_content_when_successful(self):
        """Test that fetchers extract content when fetch is successful."""
        url = "https://www.gov.uk/student-visa"
        metadata = {
            "country": "UK",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        result = fetch_uk_student(url, metadata)
        
        # If successful, should have content
        if result.success:
            assert len(result.raw_text) > 0
            assert result.fetched_at is not None
            assert "page_title" in result.metadata or "content_length" in result.metadata

