"""Versioning utilities for policy versions."""

from typing import Optional
from api.models.db.policy_version import PolicyVersion


def is_version_immutable(version: PolicyVersion) -> bool:
    """
    Validate that a PolicyVersion is immutable (should never be updated).
    
    This is a helper function to enforce immutability at the application level.
    PolicyVersions should only be created, never updated.
    
    Args:
        version: PolicyVersion instance
        
    Returns:
        True (versions are always immutable)
        
    Note:
        This function exists to document the immutability requirement.
        Actual enforcement happens at the repository level (no update method).
    """
    return True


def validate_hash_length(content_hash: str) -> bool:
    """
    Validate that a hash is exactly 64 characters (SHA256 hex).
    
    Args:
        content_hash: Hash string to validate
        
    Returns:
        True if hash is valid length
        
    Raises:
        ValueError: If hash is not 64 characters
    """
    if len(content_hash) != 64:
        raise ValueError(f"Hash must be exactly 64 characters, got {len(content_hash)}")
    return True



