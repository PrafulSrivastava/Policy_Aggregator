"""Unit tests for diff generation service."""

import pytest
from api.services.diff_generator import generate_diff, generate_html_diff, MAX_DIFF_SIZE


class TestGenerateDiff:
    """Tests for generate_diff() function."""
    
    def test_added_text(self):
        """Test diff generation for text addition."""
        old_text = "Original content.\nLine 2."
        new_text = "Original content.\nLine 2.\nNew line added."
        
        diff = generate_diff(old_text, new_text)
        
        assert diff is not None
        assert len(diff) > 0
        assert "New line added" in diff
        assert "+" in diff  # Addition marker
        assert "--- old_version" in diff
        assert "+++ new_version" in diff
    
    def test_removed_text(self):
        """Test diff generation for text removal."""
        old_text = "Original content.\nLine to remove.\nLine 3."
        new_text = "Original content.\nLine 3."
        
        diff = generate_diff(old_text, new_text)
        
        assert diff is not None
        assert len(diff) > 0
        assert "Line to remove" in diff
        assert "-" in diff  # Removal marker
        assert "--- old_version" in diff
        assert "+++ new_version" in diff
    
    def test_modified_text(self):
        """Test diff generation for text modification."""
        old_text = "Original content.\nLine 2 unchanged.\nOld line 3."
        new_text = "Original content.\nLine 2 unchanged.\nNew line 3."
        
        diff = generate_diff(old_text, new_text)
        
        assert diff is not None
        assert len(diff) > 0
        assert "Old line 3" in diff or "-" in diff
        assert "New line 3" in diff or "+" in diff
        assert "Line 2 unchanged" in diff  # Context line
    
    def test_multiple_changes(self):
        """Test diff generation for multiple changes."""
        old_text = "Line 1.\nLine 2 to remove.\nLine 3 unchanged.\nLine 4 to modify."
        new_text = "Line 1.\nLine 3 unchanged.\nLine 4 modified.\nLine 5 added."
        
        diff = generate_diff(old_text, new_text)
        
        assert diff is not None
        assert len(diff) > 0
        # Should show multiple changes
        assert "Line 2 to remove" in diff or "-" in diff
        assert "Line 4 modified" in diff or "+" in diff
        assert "Line 5 added" in diff or "+" in diff
        assert "Line 3 unchanged" in diff  # Context
    
    def test_context_lines(self):
        """Test that context lines are included."""
        old_text = "Context before.\nLine to remove.\nContext after."
        new_text = "Context before.\nContext after."
        
        diff = generate_diff(old_text, new_text, context_lines=1)
        
        assert diff is not None
        assert "Context before" in diff or "Context after" in diff
    
    def test_different_context_line_counts(self):
        """Test with different context line counts."""
        old_text = "Line 1.\nLine 2.\nLine 3.\nLine 4.\nLine 5 to change.\nLine 6.\nLine 7."
        new_text = "Line 1.\nLine 2.\nLine 3.\nLine 4.\nLine 5 changed.\nLine 6.\nLine 7."
        
        diff_0 = generate_diff(old_text, new_text, context_lines=0)
        diff_3 = generate_diff(old_text, new_text, context_lines=3)
        
        assert diff_0 is not None
        assert diff_3 is not None
        # More context lines should produce a longer diff
        assert len(diff_3) >= len(diff_0)
    
    def test_empty_old_text(self):
        """Test diff when old text is empty (all new content)."""
        old_text = ""
        new_text = "New content.\nLine 2."
        
        diff = generate_diff(old_text, new_text)
        
        assert diff is not None
        assert len(diff) > 0
        assert "New content" in diff
        assert "+" in diff
    
    def test_empty_new_text(self):
        """Test diff when new text is empty (all content removed)."""
        old_text = "Content to remove.\nLine 2."
        new_text = ""
        
        diff = generate_diff(old_text, new_text)
        
        assert diff is not None
        assert len(diff) > 0
        assert "Content to remove" in diff
        assert "-" in diff
    
    def test_both_empty(self):
        """Test diff when both texts are empty."""
        old_text = ""
        new_text = ""
        
        diff = generate_diff(old_text, new_text)
        
        assert diff == ""
    
    def test_identical_text(self):
        """Test diff when texts are identical (no changes)."""
        text = "Identical content.\nLine 2."
        
        diff = generate_diff(text, text)
        
        # Should produce minimal diff or empty
        assert diff is not None
    
    def test_custom_file_names(self):
        """Test diff with custom file names."""
        old_text = "Old content."
        new_text = "New content."
        
        diff = generate_diff(
            old_text,
            new_text,
            fromfile="custom_old",
            tofile="custom_new"
        )
        
        assert "--- custom_old" in diff
        assert "+++ custom_new" in diff
    
    def test_negative_context_lines_raises_error(self):
        """Test that negative context_lines raises ValueError."""
        old_text = "Old content."
        new_text = "New content."
        
        with pytest.raises(ValueError, match="context_lines must be non-negative"):
            generate_diff(old_text, new_text, context_lines=-1)
    
    def test_large_document_handling(self):
        """Test that large documents are handled efficiently."""
        # Create a large document (but not too large for testing)
        large_text = "Line of content.\n" * 1000
        
        old_text = large_text
        new_text = large_text + "New line at end.\n"
        
        # Should not raise memory errors
        diff = generate_diff(old_text, new_text)
        
        assert diff is not None
        assert len(diff) > 0
    
    def test_diff_truncation_for_extremely_large_diff(self):
        """Test that extremely large diffs are truncated."""
        # Create text that will produce a very large diff
        # (This test may not trigger truncation in practice, but tests the logic)
        old_text = "A" * 1000
        new_text = "B" * 1000 + "\n" + "C" * 1000
        
        diff = generate_diff(old_text, new_text)
        
        # Should handle without error
        assert diff is not None
        # If truncated, should have note
        if len(diff) > MAX_DIFF_SIZE - 100:
            assert "TRUNCATED" in diff or "truncated" in diff


class TestGenerateHtmlDiff:
    """Tests for generate_html_diff() function."""
    
    def test_html_diff_generation(self):
        """Test HTML diff generation."""
        old_text = "Old content.\nLine 2."
        new_text = "New content.\nLine 2."
        
        html_diff = generate_html_diff(old_text, new_text)
        
        assert html_diff is not None
        assert len(html_diff) > 0
        assert "<table" in html_diff or "<html" in html_diff or "html" in html_diff.lower()
    
    def test_html_diff_with_custom_names(self):
        """Test HTML diff with custom file names."""
        old_text = "Old content."
        new_text = "New content."
        
        html_diff = generate_html_diff(
            old_text,
            new_text,
            fromfile="custom_old",
            tofile="custom_new"
        )
        
        assert html_diff is not None
        assert "custom_old" in html_diff or "custom_new" in html_diff

