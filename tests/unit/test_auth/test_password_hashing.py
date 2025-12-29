"""Unit tests for password hashing utilities."""

import pytest
from api.auth.auth import get_password_hash, verify_password


class TestPasswordHashing:
    """Tests for password hashing functions."""
    
    def test_get_password_hash(self):
        """Test password hashing generates a hash."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt hash format
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        result = verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        wrong_password = "wrong_password"
        
        result = verify_password(wrong_password, hashed)
        
        assert result is False
    
    def test_verify_password_different_passwords(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"
        
        hashed1 = get_password_hash(password1)
        hashed2 = get_password_hash(password2)
        
        assert hashed1 != hashed2
        assert verify_password(password1, hashed1) is True
        assert verify_password(password2, hashed2) is True
        assert verify_password(password1, hashed2) is False
        assert verify_password(password2, hashed1) is False
    
    def test_verify_password_same_password_different_hash(self):
        """Test that same password produces different hashes (salt)."""
        password = "same_password"
        
        hashed1 = get_password_hash(password)
        hashed2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hashed1 != hashed2
        
        # But both should verify correctly
        assert verify_password(password, hashed1) is True
        assert verify_password(password, hashed2) is True

