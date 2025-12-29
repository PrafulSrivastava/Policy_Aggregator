"""Hashing utilities for policy content."""

import hashlib
from typing import Union


def generate_hash(content: Union[str, bytes]) -> str:
    """
    Generate SHA256 hash for policy content.
    
    Args:
        content: String or bytes content to hash
        
    Returns:
        SHA256 hash as hexadecimal string (64 characters)
        
    Raises:
        TypeError: If content is not str or bytes
    """
    if isinstance(content, str):
        content_bytes = content.encode('utf-8')
    elif isinstance(content, bytes):
        content_bytes = content
    else:
        raise TypeError(f"Content must be str or bytes, got {type(content)}")
    
    hash_obj = hashlib.sha256(content_bytes)
    hash_hex = hash_obj.hexdigest()
    
    # Ensure hash is exactly 64 characters
    if len(hash_hex) != 64:
        raise ValueError(f"Generated hash length is {len(hash_hex)}, expected 64")
    
    return hash_hex


def compare_hashes(old_hash: str, new_hash: str) -> bool:
    """
    Compare two hashes to determine if content has changed.
    
    Args:
        old_hash: Previous hash (64 hex characters)
        new_hash: New hash (64 hex characters)
        
    Returns:
        True if hashes are different (content changed), False if same
        
    Raises:
        ValueError: If hashes are not 64 characters
    """
    if len(old_hash) != 64:
        raise ValueError(f"Old hash must be 64 characters, got {len(old_hash)}")
    if len(new_hash) != 64:
        raise ValueError(f"New hash must be 64 characters, got {len(new_hash)}")
    
    return old_hash.lower() != new_hash.lower()



