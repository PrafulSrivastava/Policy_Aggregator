"""Unit tests for content normalizer."""

import pytest
import re
import time
from api.services.normalizer import (
    normalize,
    normalize_whitespace,
    normalize_line_breaks,
    remove_boilerplate,
    preserve_structure
)
from api.services.normalization_rules import get_normalization_rules, NormalizationRule


class TestNormalizeWhitespace:
    """Tests for whitespace normalization."""
    
    def test_strip_leading_trailing_whitespace(self):
        """Test stripping leading and trailing whitespace from lines."""
        text = "  Hello World  \n  Test Content  \n  Another Line  "
        result = normalize_whitespace(text)
        
        assert result == "Hello World\nTest Content\nAnother Line"
        assert "  Hello" not in result
        assert "Content  " not in result
    
    def test_normalize_multiple_spaces(self):
        """Test normalizing multiple spaces to single space."""
        text = "Hello    World    Test"
        result = normalize_whitespace(text)
        
        assert result == "Hello World Test"
        assert "    " not in result
    
    def test_normalize_tabs(self):
        """Test normalizing tabs to spaces."""
        text = "Hello\t\tWorld\tTest"
        result = normalize_whitespace(text)
        
        # Tabs should be normalized to single space
        assert "\t" not in result
        assert "Hello World Test" in result
    
    def test_preserve_line_breaks(self):
        """Test that line breaks are preserved."""
        text = "Line 1\nLine 2\nLine 3"
        result = normalize_whitespace(text)
        
        assert "\n" in result
        assert result.count("\n") == 2
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
    
    def test_preserve_paragraph_breaks(self):
        """Test that paragraph breaks (double newlines) are preserved."""
        text = "Paragraph 1\n\nParagraph 2"
        result = normalize_whitespace(text)
        
        assert "\n\n" in result
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result


class TestNormalizeLineBreaks:
    """Tests for line break normalization."""
    
    def test_windows_line_endings(self):
        """Test converting Windows line endings (\r\n) to Unix (\n)."""
        text = "Line 1\r\nLine 2\r\nLine 3"
        result = normalize_line_breaks(text)
        
        assert "\r\n" not in result
        assert result.count("\n") == 2
        assert "Line 1\nLine 2\nLine 3" == result
    
    def test_mac_line_endings(self):
        """Test converting Mac line endings (\r) to Unix (\n)."""
        text = "Line 1\rLine 2\rLine 3"
        result = normalize_line_breaks(text)
        
        assert "\r" not in result
        assert result.count("\n") == 2
        assert "Line 1\nLine 2\nLine 3" == result
    
    def test_unix_line_endings_unchanged(self):
        """Test that Unix line endings (\n) remain unchanged."""
        text = "Line 1\nLine 2\nLine 3"
        result = normalize_line_breaks(text)
        
        assert result == text
    
    def test_mixed_line_endings(self):
        """Test handling mixed line endings."""
        text = "Line 1\r\nLine 2\rLine 3\nLine 4"
        result = normalize_line_breaks(text)
        
        assert "\r\n" not in result
        assert "\r" not in result
        assert result.count("\n") == 3


class TestRemoveBoilerplate:
    """Tests for boilerplate removal."""
    
    def test_remove_copyright_notice(self):
        """Test removing copyright notices."""
        text = "Copyright © 2024 Government Agency\n\nMain content here"
        result = remove_boilerplate(text)
        
        assert "Copyright" not in result
        assert "Main content here" in result
    
    def test_remove_page_numbers(self):
        """Test removing page numbers."""
        text = "Content here\n\nPage 1 of 5\nMore content"
        result = remove_boilerplate(text)
        
        assert "Page 1 of 5" not in result
        assert "Content here" in result
        assert "More content" in result
    
    def test_remove_last_updated(self):
        """Test removing 'Last updated' timestamps."""
        text = "Content here\n\nLast updated: 2024-01-27\nMore content"
        result = remove_boilerplate(text)
        
        assert "Last updated" not in result
        assert "Content here" in result
    
    def test_remove_navigation_items(self):
        """Test removing navigation menu items."""
        text = "Home | About | Contact\n\nMain content here"
        result = remove_boilerplate(text)
        
        # Navigation items should be removed
        assert "Home" not in result or "Main content here" in result
    
    def test_preserve_content(self):
        """Test that actual content is preserved."""
        text = "This is important policy content.\n\nMore important information here."
        result = remove_boilerplate(text)
        
        assert "important policy content" in result
        assert "More important information" in result
    
    def test_custom_rules(self):
        """Test applying custom normalization rules."""
        source_metadata = {
            'normalization_rules': [
                {
                    'pattern': r'^REMOVE THIS.*?$',
                    'replacement': '',
                    'flags': re.MULTILINE,
                    'description': 'Custom removal rule'
                }
            ]
        }
        
        text = "Keep this\nREMOVE THIS LINE\nKeep this too"
        result = remove_boilerplate(text, source_metadata)
        
        assert "REMOVE THIS LINE" not in result
        assert "Keep this" in result
        assert "Keep this too" in result


class TestPreserveStructure:
    """Tests for structure preservation."""
    
    def test_preserve_paragraph_breaks(self):
        """Test that paragraph breaks are preserved."""
        text = "Paragraph 1\n\nParagraph 2"
        result = preserve_structure(text)
        
        assert "\n\n" in result
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
    
    def test_normalize_excessive_blank_lines(self):
        """Test that excessive blank lines are normalized."""
        text = "Paragraph 1\n\n\n\n\nParagraph 2"
        result = preserve_structure(text)
        
        # Should normalize 3+ newlines to double newline
        assert "\n\n\n" not in result
        assert "\n\n" in result
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
    
    def test_remove_trailing_newlines(self):
        """Test that trailing newlines are removed."""
        text = "Content here\n\n\n"
        result = preserve_structure(text)
        
        assert not result.endswith("\n\n")
        assert "Content here" in result


class TestNormalize:
    """Tests for main normalize() function."""
    
    def test_complete_normalization_example(self):
        """Test complete normalization with before/after example."""
        # Before: messy text with various issues
        before = "  Hello    World  \r\n\r\n  Copyright © 2024  \r\n  Test   Content  "
        
        # After: clean, normalized text
        after = normalize(before)
        
        assert "Hello World" in after
        assert "Test Content" in after
        assert "Copyright" not in after
        assert "\r\n" not in after
        assert "    " not in after
        assert not after.startswith("  ")
        assert not after.endswith("  ")
    
    def test_empty_text(self):
        """Test handling empty text."""
        result = normalize("")
        assert result == ""
    
    def test_whitespace_only(self):
        """Test handling whitespace-only text."""
        result = normalize("   \n\n   \t\t  ")
        assert result == ""
    
    def test_preserve_paragraph_structure(self):
        """Test that paragraph structure is preserved."""
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        result = normalize(text)
        
        assert "\n\n" in result
        assert result.count("\n\n") == 2
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
        assert "Paragraph 3" in result
    
    def test_windows_line_endings(self):
        """Test normalization with Windows line endings."""
        text = "Line 1\r\nLine 2\r\nLine 3"
        result = normalize(text)
        
        assert "\r\n" not in result
        assert "\r" not in result
        assert "Line 1\nLine 2\nLine 3" in result
    
    def test_mac_line_endings(self):
        """Test normalization with Mac line endings."""
        text = "Line 1\rLine 2\rLine 3"
        result = normalize(text)
        
        assert "\r" not in result
        assert "Line 1\nLine 2\nLine 3" in result
    
    def test_multiple_spaces_normalized(self):
        """Test that multiple spaces are normalized."""
        text = "Hello    World    Test"
        result = normalize(text)
        
        assert "    " not in result
        assert "Hello World Test" in result
    
    def test_boilerplate_removal(self):
        """Test that boilerplate is removed."""
        text = "Main content\n\nCopyright © 2024\n\nMore content"
        result = normalize(text)
        
        assert "Copyright" not in result
        assert "Main content" in result
        assert "More content" in result
    
    def test_disable_boilerplate_removal(self):
        """Test disabling boilerplate removal."""
        text = "Main content\n\nCopyright © 2024\n\nMore content"
        result = normalize(text, remove_boilerplate_enabled=False)
        
        # Copyright should still be present
        assert "Copyright" in result
        assert "Main content" in result
    
    def test_custom_normalization_rules(self):
        """Test applying custom normalization rules."""
        source_metadata = {
            'normalization_rules': [
                {
                    'pattern': r'^CUSTOM REMOVE.*?$',
                    'replacement': '',
                    'flags': re.MULTILINE,
                    'description': 'Custom rule'
                }
            ]
        }
        
        text = "Keep this\nCUSTOM REMOVE THIS\nKeep this too"
        result = normalize(text, source_metadata)
        
        assert "CUSTOM REMOVE THIS" not in result
        assert "Keep this" in result
    
    def test_deterministic_output(self):
        """Test that normalization is deterministic."""
        text = "  Hello    World  \r\n  Test   Content  "
        
        result1 = normalize(text)
        result2 = normalize(text)
        result3 = normalize(text)
        
        # Same input should always produce same output
        assert result1 == result2 == result3
    
    def test_large_document_performance(self):
        """Test performance with large document."""
        # Create a large document (100KB+)
        large_text = "Line with content here.\n\n" * 5000  # ~100KB
        
        start_time = time.time()
        result = normalize(large_text)
        elapsed_time = time.time() - start_time
        
        # Should complete in reasonable time (< 1 second)
        assert elapsed_time < 1.0, f"Normalization took {elapsed_time:.2f}s, expected < 1s"
        assert len(result) > 0
    
    def test_very_large_document(self):
        """Test handling very large documents."""
        # Create a very large document (1MB+)
        very_large_text = "Content line here.\n\n" * 50000  # ~1MB
        
        start_time = time.time()
        result = normalize(very_large_text)
        elapsed_time = time.time() - start_time
        
        # Should complete without errors
        assert result is not None
        assert len(result) > 0
        # Should complete in reasonable time (< 5 seconds for very large)
        assert elapsed_time < 5.0, f"Normalization took {elapsed_time:.2f}s"
    
    def test_edge_case_empty_lines(self):
        """Test handling of edge case with many empty lines."""
        text = "\n\n\n\nContent\n\n\n\n"
        result = normalize(text)
        
        assert "Content" in result
        # Should normalize excessive blank lines
        assert result.count("\n\n\n") == 0
    
    def test_edge_case_single_character(self):
        """Test handling single character."""
        result = normalize("A")
        assert result == "A"
    
    def test_edge_case_special_characters(self):
        """Test handling special characters."""
        text = "Content with special chars: @#$%^&*()"
        result = normalize(text)
        
        assert "@#$%^&*()" in result
        assert "Content with special chars" in result


class TestNormalizationRules:
    """Tests for normalization rules configuration."""
    
    def test_get_default_rules(self):
        """Test getting default normalization rules."""
        rules = get_normalization_rules()
        
        assert len(rules) > 0
        assert all(isinstance(rule, NormalizationRule) for rule in rules)
    
    def test_get_custom_rules(self):
        """Test getting custom normalization rules."""
        source_metadata = {
            'normalization_rules': [
                {
                    'pattern': r'^CUSTOM.*?$',
                    'replacement': '',
                    'description': 'Custom rule'
                }
            ]
        }
        
        rules = get_normalization_rules(source_metadata)
        
        # Should include default rules plus custom rule
        assert len(rules) > len(get_normalization_rules())
        # Check that custom rule is present
        custom_rule = next((r for r in rules if 'CUSTOM' in r.pattern.pattern), None)
        assert custom_rule is not None



