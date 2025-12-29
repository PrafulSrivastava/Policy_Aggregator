"""Unit tests for FetcherManager."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from api.services.fetcher_manager import (
    load_fetchers,
    get_fetcher_for_source,
    register_fetcher,
    get_registry,
    get_metadata
)
from api.models.db.source import Source
from fetchers.base import FetchResult


@pytest.fixture
def temp_fetchers_dir():
    """Create a temporary fetchers directory for testing."""
    temp_dir = tempfile.mkdtemp()
    fetchers_dir = Path(temp_dir) / "fetchers"
    fetchers_dir.mkdir()
    
    # Create __init__.py
    (fetchers_dir / "__init__.py").write_text('"""Test fetchers package."""\n')
    
    yield fetchers_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_fetcher_module():
    """Create a mock fetcher function."""
    def mock_fetch(url: str, metadata: dict) -> FetchResult:
        return FetchResult(
            raw_text="Mock content",
            content_type="html",
            success=True
        )
    return mock_fetch


@pytest.fixture
def sample_source():
    """Create a sample Source instance for testing."""
    return Source(
        id=None,  # Will be set if needed
        country="DE",
        visa_type="Student",
        url="https://example.com/student",
        name="Germany Student Visa",
        fetch_type="html",
        check_frequency="daily",
        is_active=True,
        metadata={}
    )


class TestLoadFetchers:
    """Tests for load_fetchers() function."""
    
    def test_load_fetchers_empty_directory(self, temp_fetchers_dir):
        """Test loading fetchers from empty directory."""
        registry = load_fetchers(temp_fetchers_dir)
        assert registry == {}
    
    def test_load_fetchers_skips_init_and_base(self, temp_fetchers_dir):
        """Test that __init__.py and base.py are skipped."""
        # Create files that should be skipped
        (temp_fetchers_dir / "__init__.py").write_text("")
        (temp_fetchers_dir / "base.py").write_text("")
        (temp_fetchers_dir / "example_template.py").write_text("")
        
        registry = load_fetchers(temp_fetchers_dir)
        assert len(registry) == 0
    
    def test_load_fetchers_skips_invalid_naming(self, temp_fetchers_dir):
        """Test that files not matching naming convention are skipped."""
        # Create file with invalid naming
        (temp_fetchers_dir / "invalid_name.py").write_text("def fetch(): pass\n")
        
        registry = load_fetchers(temp_fetchers_dir)
        assert len(registry) == 0
    
    def test_load_fetchers_handles_missing_fetch_function(self, temp_fetchers_dir):
        """Test handling of modules without fetch function."""
        # Create validly named module without fetch function
        (temp_fetchers_dir / "de_bmi_student.py").write_text("def other_function(): pass\n")
        
        with patch('api.services.fetcher_manager.importlib.import_module') as mock_import:
            mock_module = MagicMock()
            del mock_module.fetch  # Remove fetch attribute
            mock_import.return_value = mock_module
            
            registry = load_fetchers(temp_fetchers_dir)
            # Should handle gracefully and skip
            assert isinstance(registry, dict)
    
    def test_load_fetchers_handles_import_error(self, temp_fetchers_dir):
        """Test handling of import errors."""
        (temp_fetchers_dir / "de_bmi_student.py").write_text("invalid syntax here !!!\n")
        
        registry = load_fetchers(temp_fetchers_dir)
        # Should handle gracefully and return empty or partial registry
        assert isinstance(registry, dict)
    
    def test_load_fetchers_discovers_valid_fetcher(self, temp_fetchers_dir, mock_fetcher_module):
        """Test discovering and loading a valid fetcher."""
        # Create a valid fetcher file
        fetcher_content = '''
def fetch(url: str, metadata: dict):
    from fetchers.base import FetchResult
    return FetchResult(
        raw_text="Test content",
        content_type="html",
        success=True
    )

SOURCE_TYPE = "html"
'''
        (temp_fetchers_dir / "de_bmi_student.py").write_text(fetcher_content)
        
        # Mock importlib to return our mock module
        with patch('api.services.fetcher_manager.importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.fetch = mock_fetcher_module
            mock_module.SOURCE_TYPE = "html"
            mock_import.return_value = mock_module
            
            registry = load_fetchers(temp_fetchers_dir)
            assert len(registry) == 1
            assert "de_bmi_student" in registry
            assert callable(registry["de_bmi_student"])
    
    def test_load_fetchers_stores_metadata(self, temp_fetchers_dir, mock_fetcher_module):
        """Test that fetcher metadata is stored correctly."""
        (temp_fetchers_dir / "de_bmi_student.py").write_text("def fetch(): pass\n")
        
        with patch('api.services.fetcher_manager.importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.fetch = mock_fetcher_module
            mock_module.SOURCE_TYPE = "html"
            mock_import.return_value = mock_module
            
            load_fetchers(temp_fetchers_dir)
            metadata = get_metadata()
            assert "de_bmi_student" in metadata
            assert metadata["de_bmi_student"]["source_type"] == "html"


class TestGetFetcherForSource:
    """Tests for get_fetcher_for_source() function."""
    
    def test_get_fetcher_empty_registry(self, sample_source):
        """Test getting fetcher when registry is empty."""
        # Clear registry
        with patch('api.services.fetcher_manager._fetcher_registry', {}):
            result = get_fetcher_for_source(sample_source)
            # Should attempt to load, then return None if still empty
            assert result is None or callable(result)
    
    def test_get_fetcher_no_match(self, sample_source, mock_fetcher_module):
        """Test getting fetcher when no match exists."""
        # Clear registry first
        from api.services.fetcher_manager import get_registry
        registry = get_registry()
        registry.clear()
        
        # Register a fetcher that doesn't match (different country)
        register_fetcher("us_dhs_work", mock_fetcher_module, {"source_type": "html"})
        
        result = get_fetcher_for_source(sample_source)
        assert result is None
    
    def test_get_fetcher_matches_by_country_and_visa_type(self, sample_source, mock_fetcher_module):
        """Test matching fetcher by country and visa type."""
        # Register matching fetcher
        register_fetcher("de_bmi_student", mock_fetcher_module, {"source_type": "html"})
        
        result = get_fetcher_for_source(sample_source)
        assert result is not None
        assert callable(result)
    
    def test_get_fetcher_matches_by_fetch_type(self, sample_source, mock_fetcher_module):
        """Test matching fetcher by fetch type."""
        # Register fetcher with matching fetch type
        register_fetcher("de_bmi_student", mock_fetcher_module, {"source_type": "html"})
        
        result = get_fetcher_for_source(sample_source)
        assert result is not None
        
        # Test with non-matching fetch type
        sample_source.fetch_type = "pdf"
        result = get_fetcher_for_source(sample_source)
        assert result is None
    
    def test_get_fetcher_handles_multiple_matches(self, sample_source, mock_fetcher_module):
        """Test handling multiple matching fetchers."""
        # Register multiple matching fetchers
        register_fetcher("de_bmi_student", mock_fetcher_module, {"source_type": "html"})
        register_fetcher("de_bmi_student_alt", mock_fetcher_module, {"source_type": "html"})
        
        result = get_fetcher_for_source(sample_source)
        # Should return first match
        assert result is not None
        assert callable(result)


class TestFetcherRegistry:
    """Tests for fetcher registry functionality."""
    
    def test_register_fetcher(self, mock_fetcher_module):
        """Test manually registering a fetcher."""
        register_fetcher("test_fetcher", mock_fetcher_module, {"source_type": "html"})
        
        registry = get_registry()
        assert "test_fetcher" in registry
        assert registry["test_fetcher"] == mock_fetcher_module
    
    def test_register_fetcher_stores_metadata(self, mock_fetcher_module):
        """Test that registered fetcher metadata is stored."""
        metadata = {"source_type": "pdf", "custom_field": "value"}
        register_fetcher("test_fetcher", mock_fetcher_module, metadata)
        
        stored_metadata = get_metadata()
        assert "test_fetcher" in stored_metadata
        assert stored_metadata["test_fetcher"] == metadata
    
    def test_register_fetcher_invalid_function(self):
        """Test that registering non-callable raises error."""
        with pytest.raises(ValueError, match="must be callable"):
            register_fetcher("test", "not a function", {})
    
    def test_get_registry_returns_copy(self, mock_fetcher_module):
        """Test that get_registry returns a copy, not the original."""
        register_fetcher("test_fetcher", mock_fetcher_module, {})
        
        registry1 = get_registry()
        registry2 = get_registry()
        
        # Should be different objects
        assert registry1 is not registry2
        # But should have same content
        assert registry1 == registry2
    
    def test_get_metadata_returns_copy(self, mock_fetcher_module):
        """Test that get_metadata returns a copy."""
        register_fetcher("test_fetcher", mock_fetcher_module, {"key": "value"})
        
        metadata1 = get_metadata()
        metadata2 = get_metadata()
        
        # Should be different objects
        assert metadata1 is not metadata2
        # But should have same content
        assert metadata1 == metadata2


class TestFetcherIntegration:
    """Integration tests for fetcher system."""
    
    def test_full_workflow(self, temp_fetchers_dir, sample_source):
        """Test full workflow: load fetchers, get fetcher, execute fetch."""
        # Create a simple fetcher file
        fetcher_content = '''
from fetchers.base import FetchResult

def fetch(url: str, metadata: dict) -> FetchResult:
    return FetchResult(
        raw_text=f"Fetched from {url}",
        content_type="html",
        success=True,
        metadata={"url": url}
    )

SOURCE_TYPE = "html"
'''
        (temp_fetchers_dir / "de_bmi_student.py").write_text(fetcher_content)
        
        # Load fetchers
        with patch('api.services.fetcher_manager.importlib.import_module') as mock_import:
            # Create a real module-like object
            import types
            mock_module = types.ModuleType('fetchers.de_bmi_student')
            
            def fetch_func(url: str, metadata: dict) -> FetchResult:
                return FetchResult(
                    raw_text=f"Fetched from {url}",
                    content_type="html",
                    success=True
                )
            
            mock_module.fetch = fetch_func
            mock_module.SOURCE_TYPE = "html"
            mock_import.return_value = mock_module
            
            registry = load_fetchers(temp_fetchers_dir)
            assert len(registry) == 1
            
            # Get fetcher for source
            fetcher = get_fetcher_for_source(sample_source)
            assert fetcher is not None
            
            # Execute fetch
            result = fetcher("https://example.com", {})
            assert isinstance(result, FetchResult)
            assert result.success is True
            assert result.content_type == "html"



