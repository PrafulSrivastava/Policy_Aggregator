"""Unit tests for hashing utilities."""

import pytest
from api.utils.hashing import generate_hash, compare_hashes


class TestGenerateHash:
    """Tests for generate_hash function."""
    
    def test_generate_hash_string(self):
        """Test hash generation from string."""
        content = "test content"
        hash_result = generate_hash(content)
        
        assert len(hash_result) == 64
        assert isinstance(hash_result, str)
        assert all(c in '0123456789abcdef' for c in hash_result)
    
    def test_generate_hash_bytes(self):
        """Test hash generation from bytes."""
        content = b"test content"
        hash_result = generate_hash(content)
        
        assert len(hash_result) == 64
        assert isinstance(hash_result, str)
    
    def test_generate_hash_empty_string(self):
        """Test hash generation from empty string."""
        content = ""
        hash_result = generate_hash(content)
        
        assert len(hash_result) == 64
        # Empty string should produce a known hash
        assert hash_result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    def test_generate_hash_long_text(self):
        """Test hash generation from long text."""
        content = "a" * 10000
        hash_result = generate_hash(content)
        
        assert len(hash_result) == 64
    
    def test_generate_hash_special_characters(self):
        """Test hash generation with special characters."""
        content = "test!@#$%^&*()_+-=[]{}|;':\",./<>?"
        hash_result = generate_hash(content)
        
        assert len(hash_result) == 64
    
    def test_generate_hash_unicode(self):
        """Test hash generation with unicode characters."""
        content = "test 测试 🚀"
        hash_result = generate_hash(content)
        
        assert len(hash_result) == 64
    
    def test_generate_hash_deterministic(self):
        """Test that same content produces same hash."""
        content = "test content"
        hash1 = generate_hash(content)
        hash2 = generate_hash(content)
        
        assert hash1 == hash2
    
    def test_generate_hash_different_content(self):
        """Test that different content produces different hashes."""
        hash1 = generate_hash("content 1")
        hash2 = generate_hash("content 2")
        
        assert hash1 != hash2
    
    def test_generate_hash_invalid_type(self):
        """Test that invalid type raises TypeError."""
        with pytest.raises(TypeError):
            generate_hash(123)
        
        with pytest.raises(TypeError):
            generate_hash(None)


class TestCompareHashes:
    """Tests for compare_hashes function."""
    
    def test_compare_hashes_different(self):
        """Test comparing different hashes."""
        old_hash = "a" * 64
        new_hash = "b" * 64
        
        result = compare_hashes(old_hash, new_hash)
        assert result is True  # Hashes are different
    
    def test_compare_hashes_same(self):
        """Test comparing same hashes."""
        hash_value = "a" * 64
        
        result = compare_hashes(hash_value, hash_value)
        assert result is False  # Hashes are same
    
    def test_compare_hashes_case_insensitive(self):
        """Test that hash comparison is case insensitive."""
        old_hash = "a" * 64
        new_hash = "A" * 64
        
        result = compare_hashes(old_hash, new_hash)
        assert result is False  # Same hash, different case
    
    def test_compare_hashes_invalid_length_old(self):
        """Test that invalid old hash length raises ValueError."""
        with pytest.raises(ValueError, match="Old hash must be 64 characters"):
            compare_hashes("short", "b" * 64)
    
    def test_compare_hashes_invalid_length_new(self):
        """Test that invalid new hash length raises ValueError."""
        with pytest.raises(ValueError, match="New hash must be 64 characters"):
            compare_hashes("a" * 64, "short")



