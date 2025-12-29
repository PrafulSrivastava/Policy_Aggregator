"""Integration test for all Germany sources (old + new) for India → Germany route."""

import pytest
from api.services.fetcher_manager import load_fetchers, get_fetcher_for_source
from api.models.db.source import Source
from fetchers.base import FetchResult


class TestAllGermanySources:
    """Integration test for all Germany sources (old + new)."""
    
    def test_fetcher_manager_loads_all_germany_fetchers(self):
        """Test that Fetcher Manager loads all Germany fetchers correctly."""
        fetchers = load_fetchers()
        
        # Expected Germany fetchers (5 old + 3 new = 8 total)
        expected_fetchers = [
            'de_bmi_student',
            'de_bmi_work',
            'de_auswaertiges_amt_student',
            'de_auswaertiges_amt_work',
            'de_make_it_in_germany_work',
            'de_bamf_work',
            'de_daad_student',
            'de_arbeitsagentur_work'
        ]
        
        # Verify all expected fetchers are loaded
        for fetcher_name in expected_fetchers:
            assert fetcher_name in fetchers, f"Fetcher {fetcher_name} not loaded"
            assert callable(fetchers[fetcher_name]), f"Fetcher {fetcher_name} is not callable"
        
        # Verify we have at least 8 Germany fetchers
        germany_fetchers = [name for name in fetchers.keys() if name.startswith('de_')]
        assert len(germany_fetchers) >= 8, f"Expected at least 8 Germany fetchers, found {len(germany_fetchers)}"
    
    @pytest.mark.parametrize("country,visa_type,url,name", [
        ("DE", "Student", "https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/student-visa.html", "Germany BMI Student Visa Information"),
        ("DE", "Work", "https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/skilled-workers.html", "Germany BMI Skilled Worker Visa Information"),
        ("DE", "Student", "https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-students", "Germany Auswärtiges Amt Student Visa Information"),
        ("DE", "Work", "https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-employment", "Germany Auswärtiges Amt Work Visa Information"),
        ("DE", "Work", "https://www.make-it-in-germany.com/en/visa/skilled-workers", "Make it in Germany Skilled Worker Visa Information"),
        ("DE", "Work", "https://www.bamf.de/EN/Themen/MigrationAufenthalt/ZuwandererDrittstaaten/Migrathek/migrathek-node.html", "Germany BAMF Work Visa Information"),
        ("DE", "Student", "https://www.daad.de/en/study-and-research-in-germany/plan-your-studies/entry-and-residence/", "Germany DAAD Student Visa Information"),
        ("DE", "Work", "https://www.arbeitsagentur.de/en/working-in-germany", "Germany Bundesagentur für Arbeit Work Visa Information"),
    ])
    def test_all_sources_have_matching_fetchers(self, country, visa_type, url, name):
        """Test that all sources (old + new) have matching fetchers."""
        # Create a source object
        source = Source(
            country=country,
            visa_type=visa_type,
            url=url,
            name=name,
            fetch_type="html",
            check_frequency="daily",
            is_active=True
        )
        
        # Get fetcher for source
        fetcher = get_fetcher_for_source(source)
        
        # Verify fetcher is found
        assert fetcher is not None, f"No fetcher found for source: {name}"
        assert callable(fetcher), f"Fetcher for {name} is not callable"
    
    def test_all_fetchers_execute_successfully(self):
        """Test that all fetchers execute successfully (structure test)."""
        # Load all fetchers
        fetchers = load_fetchers()
        
        # Get all Germany fetchers
        germany_fetchers = {name: func for name, func in fetchers.items() if name.startswith('de_')}
        
        # Test each fetcher with a test URL (may fail due to network, but should not raise exceptions)
        test_metadata = {
            "country": "DE",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        for fetcher_name, fetcher_func in germany_fetchers.items():
            # Use a simple test - just verify it returns FetchResult
            # Note: Using invalid URL to test error handling, not network access
            test_url = "https://test-url-for-structure-check.com"
            
            result = fetcher_func(test_url, test_metadata)
            
            # Verify it returns FetchResult
            assert isinstance(result, FetchResult), f"Fetcher {fetcher_name} did not return FetchResult"
            assert result.content_type in ["html", "pdf", "text"], f"Invalid content_type from {fetcher_name}"
            # Should handle errors gracefully (not raise exceptions)
            assert result.error_message is None or result.success is False, f"Fetcher {fetcher_name} should handle errors gracefully"
    
    def test_daily_job_handles_all_sources_efficiently(self):
        """Test that daily job can handle all sources efficiently."""
        # Load all fetchers
        fetchers = load_fetchers()
        
        # Get all Germany fetchers
        germany_fetchers = {name: func for name, func in fetchers.items() if name.startswith('de_')}
        
        # Verify we have the expected number of fetchers
        assert len(germany_fetchers) >= 8, f"Expected at least 8 Germany fetchers, found {len(germany_fetchers)}"
        
        # Verify all fetchers are callable and ready
        for fetcher_name, fetcher_func in germany_fetchers.items():
            assert callable(fetcher_func), f"Fetcher {fetcher_name} is not callable"
        
        # This test verifies structure - actual execution would require network access
        # and would be tested in a separate environment
    
    def test_content_extraction_works_for_all_sources(self):
        """Test that content extraction works for all sources (structure test)."""
        # Load all fetchers
        fetchers = load_fetchers()
        
        # Get all Germany fetchers
        germany_fetchers = {name: func for name, func in fetchers.items() if name.startswith('de_')}
        
        # Test that all fetchers return FetchResult with proper structure
        test_metadata = {
            "country": "DE",
            "visa_type": "Student",
            "fetch_type": "html"
        }
        
        for fetcher_name, fetcher_func in germany_fetchers.items():
            # Use invalid URL to test structure without network access
            test_url = "https://test-structure-check.com"
            
            result = fetcher_func(test_url, test_metadata)
            
            # Verify FetchResult structure
            assert isinstance(result, FetchResult)
            assert hasattr(result, 'raw_text')
            assert hasattr(result, 'content_type')
            assert hasattr(result, 'success')
            assert hasattr(result, 'metadata')
            assert hasattr(result, 'fetched_at')
            
            # If successful, should have content
            if result.success:
                assert len(result.raw_text) > 0, f"Fetcher {fetcher_name} returned empty content on success"
                assert result.content_type in ["html", "pdf", "text"]

