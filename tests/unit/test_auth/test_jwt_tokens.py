"""Unit tests for JWT token generation and validation."""

import pytest
from datetime import datetime, timedelta
from jose import JWTError
from api.auth.auth import create_access_token, decode_access_token


class TestJWTTokens:
    """Tests for JWT token functions."""
    
    def test_create_access_token(self):
        """Test creating a JWT access token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_access_token_valid(self):
        """Test decoding a valid JWT token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert "sub" in payload
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    
    def test_decode_access_token_invalid(self):
        """Test decoding an invalid JWT token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(JWTError):
            decode_access_token(invalid_token)
    
    def test_create_access_token_with_expires_delta(self):
        """Test creating token with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(hours=1)
        
        # Capture time before token creation
        before_token = datetime.utcnow()
        token = create_access_token(data, expires_delta=expires_delta)
        after_token = datetime.utcnow()
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert "exp" in payload
        
        # Check expiration is approximately 1 hour from token creation time
        exp_timestamp = payload["exp"]
        # JWT exp is in UTC, so use utcfromtimestamp
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        
        # The token should expire 1 hour from when it was created
        # Token was created between before_token and after_token, so expiration should be
        # between (before_token + 1 hour - small tolerance) and (after_token + 1 hour + small tolerance)
        # Calculate expected expiration times with tolerance for microsecond precision
        expected_exp_min = before_token + expires_delta - timedelta(seconds=1)  # Allow 1s tolerance for rounding
        expected_exp_max = after_token + expires_delta + timedelta(seconds=5)  # Allow 5s tolerance
        
        # Verify expiration is in the expected range
        assert expected_exp_min <= exp_datetime <= expected_exp_max, \
            f"Expiration {exp_datetime} not in range [{expected_exp_min}, {expected_exp_max}]. " \
            f"Token created between {before_token} and {after_token}, expires_delta={expires_delta}"
    
    def test_token_expiration(self):
        """Test that expired tokens cannot be decoded."""
        data = {"sub": "testuser"}
        # Create token with negative expiration (already expired)
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires_delta)
        
        with pytest.raises(JWTError):
            decode_access_token(token)
    
    def test_token_payload_includes_all_data(self):
        """Test that token includes all provided data."""
        data = {
            "sub": "testuser",
            "custom_field": "custom_value",
            "user_id": "12345"
        }
        token = create_access_token(data)
        
        payload = decode_access_token(token)
        
        assert payload["sub"] == "testuser"
        assert payload["custom_field"] == "custom_value"
        assert payload["user_id"] == "12345"
        assert "exp" in payload

