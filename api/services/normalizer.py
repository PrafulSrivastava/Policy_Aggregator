"""Content normalization service for preparing text for stable diff comparison."""

import re
import logging
from typing import Optional, Dict, List
from api.services.normalization_rules import get_normalization_rules

logger = logging.getLogger(__name__)

# Performance: compile common patterns once
WHITESPACE_PATTERN = re.compile(r'[ \t]+')  # Multiple spaces or tabs
LEADING_TRAILING_WHITESPACE = re.compile(r'^[ \t]+|[ \t]+$', re.MULTILINE)
LINE_BREAK_PATTERN = re.compile(r'\r\n|\r')  # Windows and Mac line endings


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    - Strips leading/trailing whitespace from each line
    - Normalizes multiple spaces/tabs to single space
    - Preserves line breaks and paragraph structure
    
    Args:
        text: Input text
    
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    
    # Normalize line breaks first (Windows \r\n and Mac \r to \n)
    text = LINE_BREAK_PATTERN.sub('\n', text)
    
    # Strip leading/trailing whitespace from each line
    text = LEADING_TRAILING_WHITESPACE.sub('', text)
    
    # Normalize multiple spaces/tabs to single space (but preserve newlines)
    # Process line by line to preserve structure
    lines = text.split('\n')
    normalized_lines = []
    
    for line in lines:
        # Replace multiple spaces/tabs with single space
        normalized_line = WHITESPACE_PATTERN.sub(' ', line)
        normalized_lines.append(normalized_line)
    
    return '\n'.join(normalized_lines)


def remove_boilerplate(text: str, source_metadata: Optional[Dict] = None) -> str:
    """
    Remove common boilerplate patterns from text.
    
    Removes headers, footers, navigation, and other non-content elements
    that might change without actual content changes.
    
    Args:
        text: Input text
        source_metadata: Source metadata for custom normalization rules
    
    Returns:
        Text with boilerplate removed
    """
    if not text:
        return ""
    
    rules = get_normalization_rules(source_metadata)
    
    for rule in rules:
        try:
            text = rule.pattern.sub(rule.replacement, text)
        except Exception as e:
            logger.warning(f"Error applying normalization rule '{rule.description}': {e}")
            continue
    
    return text


def normalize_line_breaks(text: str) -> str:
    """
    Normalize line breaks to Unix-style (\n).
    
    Converts Windows (\r\n) and Mac (\r) line endings to Unix (\n).
    
    Args:
        text: Input text
    
    Returns:
        Text with normalized line breaks
    """
    if not text:
        return ""
    
    # Convert Windows and Mac line endings to Unix
    return LINE_BREAK_PATTERN.sub('\n', text)


def preserve_structure(text: str) -> str:
    """
    Ensure paragraph structure is preserved.
    
    Normalizes multiple consecutive newlines to double newline (paragraph break),
    but preserves the structure.
    
    Args:
        text: Input text
    
    Returns:
        Text with preserved structure
    """
    if not text:
        return ""
    
    # Normalize 3+ consecutive newlines to double newline (paragraph break)
    # This preserves paragraph structure while removing excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove trailing newlines at start and end
    text = text.strip('\n')
    
    return text


def normalize(
    raw_text: str,
    source_metadata: Optional[Dict] = None,
    remove_boilerplate_enabled: bool = True
) -> str:
    """
    Normalize raw fetched text for stable diff comparison.
    
    This function prepares text content for change detection by:
    1. Normalizing whitespace (leading/trailing, multiple spaces)
    2. Normalizing line breaks (Windows/Unix/Mac → Unix)
    3. Removing common boilerplate (headers, footers, navigation)
    4. Preserving meaningful structure (paragraphs, sections)
    
    The normalization is deterministic: same input always produces same output.
    It does NOT perform semantic parsing or interpretation.
    
    Args:
        raw_text: Raw text content from fetcher
        source_metadata: Optional source metadata for custom normalization rules
        remove_boilerplate_enabled: Whether to remove boilerplate (default: True)
    
    Returns:
        Normalized text ready for hashing and diff comparison
    
    Example:
        >>> raw = "  Hello    World  \\r\\n\\r\\n  Test   Content  "
        >>> normalized = normalize(raw)
        >>> # Result: "Hello World\\n\\nTest Content"
    """
    if not raw_text:
        return ""
    
    # Ensure input is string and handle encoding
    if not isinstance(raw_text, str):
        try:
            text = str(raw_text)
        except Exception as e:
            logger.error(f"Error converting input to string: {e}")
            return ""
    else:
        text = raw_text
    
    # Step 1: Normalize line breaks (Windows/Mac → Unix)
    text = normalize_line_breaks(text)
    
    # Step 2: Remove boilerplate if enabled
    if remove_boilerplate_enabled:
        text = remove_boilerplate(text, source_metadata)
    
    # Step 3: Normalize whitespace
    text = normalize_whitespace(text)
    
    # Step 4: Preserve structure (normalize excessive blank lines)
    text = preserve_structure(text)
    
    # Step 5: Final trim of leading/trailing whitespace
    text = text.strip()
    
    return text





