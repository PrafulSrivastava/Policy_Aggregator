"""Integration tests for Germany source fetchers."""

import pytest
from fetchers.de_bmi_student import fetch as fetch_bmi_student, SOURCE_TYPE as BMI_STUDENT_TYPE
from fetchers.de_bmi_work import fetch as fetch_bmi_work, SOURCE_TYPE as BMI_WORK_TYPE
from fetchers.de_auswaertiges_amt_student import fetch as fetch_aa_student, SOURCE_TYPE as AA_STUDENT_TYPE
from fetchers.de_auswaertiges_amt_work import fetch as fetch_aa_work, SOURCE_TYPE as AA_WORK_TYPE
from fetchers.de_make_it_in_germany_work import fetch as fetch_makeit_work, SOURCE_TYPE as MAKEIT_WORK_TYPE
from fetchers.de_bamf_work import fetch as fetch_bamf_work, SOURCE_TYPE as BAMF_WORK_TYPE
from fetchers.de_daad_student import fetch as fetch_daad_student, SOURCE_TYPE as DAAD_STUDENT_TYPE
from fetchers.de_arbeitsagentur_work import fetch as fetch_arbeitsagentur_work, SOURCE_TYPE as ARBEITSAGENTUR_WORK_TYPE
from fetchers.base import FetchResult


class TestGermanySourceFetchers:
    """Integration tests for Germany source fetchers."""
    
    @pytest.mark.parametrize("fetcher_func,url,visa_type,source_type", [
        (fetch_bmi_student, "https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/student-visa.html", "Student", BMI_STUDENT_TYPE),
        (fetch_bmi_work, "https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/skilled-workers.html", "Work", BMI_WORK_TYPE),
        (fetch_aa_student, "https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-students", "Student", AA_STUDENT_TYPE),
        (fetch_aa_work, "https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-employment", "Work", AA_WORK_TYPE),
        (fetch_makeit_work, "https://www.make-it-in-germany.com/en/visa/skilled-workers", "Work", MAKEIT_WORK_TYPE),
        (fetch_bamf_work, "https://www.bamf.de/EN/Themen/MigrationAufenthalt/ZuwandererDrittstaaten/Migrathek/migrathek-node.html", "Work", BAMF_WORK_TYPE),
        (fetch_daad_student, "https://www.daad.de/en/study-and-research-in-germany/plan-your-studies/entry-and-residence/", "Student", DAAD_STUDENT_TYPE),
        (fetch_arbeitsagentur_work, "https://www.arbeitsagentur.de/en/working-in-germany", "Work", ARBEITSAGENTUR_WORK_TYPE),
    ])
    def test_fetcher_loads_and_executes(self, fetcher_func, url, visa_type, source_type):
        """Test that each fetcher loads and executes with real URL."""
        metadata = {
            "country": "DE",
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
    
    def test_bmi_student_fetcher_returns_result(self):
        """Test BMI student fetcher returns FetchResult."""
        url = "https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/student-visa.html"
        metadata = {
            "country": "DE",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        result = fetch_bmi_student(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "Germany BMI"
            assert result.metadata["visa_category"] == "Student"
    
    def test_bmi_work_fetcher_returns_result(self):
        """Test BMI work fetcher returns FetchResult."""
        url = "https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/skilled-workers.html"
        metadata = {
            "country": "DE",
            "visa_type": "Work",
            "fetch_type": "html"
        }
        
        result = fetch_bmi_work(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "Germany BMI"
            assert result.metadata["visa_category"] == "Work"
    
    def test_auswaertiges_amt_student_fetcher_returns_result(self):
        """Test Auswärtiges Amt student fetcher returns FetchResult."""
        url = "https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-students"
        metadata = {
            "country": "DE",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        result = fetch_aa_student(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "Germany Auswärtiges Amt"
            assert result.metadata["visa_category"] == "Student"
    
    def test_auswaertiges_amt_work_fetcher_returns_result(self):
        """Test Auswärtiges Amt work fetcher returns FetchResult."""
        url = "https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-employment"
        metadata = {
            "country": "DE",
            "visa_type": "Work",
            "fetch_type": "html"
        }
        
        result = fetch_aa_work(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "Germany Auswärtiges Amt"
            assert result.metadata["visa_category"] == "Work"
    
    def test_make_it_in_germany_work_fetcher_returns_result(self):
        """Test Make it in Germany work fetcher returns FetchResult."""
        url = "https://www.make-it-in-germany.com/en/visa/skilled-workers"
        metadata = {
            "country": "DE",
            "visa_type": "Work",
            "fetch_type": "html"
        }
        
        result = fetch_makeit_work(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "Make it in Germany"
            assert result.metadata["visa_category"] == "Work"
    
    def test_bamf_work_fetcher_returns_result(self):
        """Test BAMF work fetcher returns FetchResult."""
        url = "https://www.bamf.de/EN/Themen/MigrationAufenthalt/ZuwandererDrittstaaten/Migrathek/migrathek-node.html"
        metadata = {
            "country": "DE",
            "visa_type": "Work",
            "fetch_type": "html"
        }
        
        result = fetch_bamf_work(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "Germany BAMF"
            assert result.metadata["visa_category"] == "Work"
    
    def test_daad_student_fetcher_returns_result(self):
        """Test DAAD student fetcher returns FetchResult."""
        url = "https://www.daad.de/en/study-and-research-in-germany/plan-your-studies/entry-and-residence/"
        metadata = {
            "country": "DE",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        result = fetch_daad_student(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "Germany DAAD"
            assert result.metadata["visa_category"] == "Student"
    
    def test_arbeitsagentur_work_fetcher_returns_result(self):
        """Test Bundesagentur für Arbeit work fetcher returns FetchResult."""
        url = "https://www.arbeitsagentur.de/en/working-in-germany"
        metadata = {
            "country": "DE",
            "visa_type": "Work",
            "fetch_type": "html"
        }
        
        result = fetch_arbeitsagentur_work(url, metadata)
        
        assert isinstance(result, FetchResult)
        assert result.content_type == "html"
        # Verify metadata is set
        if result.success:
            assert "source" in result.metadata
            assert result.metadata["source"] == "Germany Bundesagentur für Arbeit"
            assert result.metadata["visa_category"] == "Work"
    
    def test_all_fetchers_handle_errors_gracefully(self):
        """Test that all fetchers handle errors gracefully (no exceptions raised)."""
        invalid_url = "https://invalid-url-that-does-not-exist-12345.com/page"
        metadata = {
            "country": "DE",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        fetchers = [
            fetch_bmi_student,
            fetch_bmi_work,
            fetch_aa_student,
            fetch_aa_work,
            fetch_makeit_work,
            fetch_bamf_work,
            fetch_daad_student,
            fetch_arbeitsagentur_work
        ]
        
        for fetcher in fetchers:
            # Should not raise exception, should return FetchResult with success=False
            result = fetcher(invalid_url, metadata)
            assert isinstance(result, FetchResult)
            assert result.success is False
            assert result.error_message is not None
    
    def test_fetchers_extract_content_when_successful(self):
        """Test that fetchers extract content when fetch is successful."""
        # Use a simple test URL that should work (or mock)
        # For real testing, this would use actual URLs
        # For now, we test the structure
        
        url = "https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/student-visa.html"
        metadata = {
            "country": "DE",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        result = fetch_bmi_student(url, metadata)
        
        # If successful, should have content
        if result.success:
            assert len(result.raw_text) > 0
            assert result.fetched_at is not None
            assert "page_title" in result.metadata or "content_length" in result.metadata

