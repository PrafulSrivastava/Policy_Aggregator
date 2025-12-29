"""Diff generation service for policy content using Python difflib."""

import difflib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Maximum diff size before truncation (10MB)
MAX_DIFF_SIZE = 10 * 1024 * 1024
# Maximum document size for efficient processing (5MB)
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024


def generate_diff(
    old_text: str,
    new_text: str,
    context_lines: int = 3,
    fromfile: str = "old_version",
    tofile: str = "new_version"
) -> str:
    """
    Generate unified diff between two text versions.
    
    Args:
        old_text: Previous version text content
        new_text: New version text content
        context_lines: Number of context lines to include around changes (default: 3)
        fromfile: Label for old version in diff header (default: "old_version")
        tofile: Label for new version in diff header (default: "new_version")
    
    Returns:
        Unified diff format string showing changes
    
    Raises:
        ValueError: If context_lines is negative
    """
    if context_lines < 0:
        raise ValueError("context_lines must be non-negative")
    
    # Handle empty text cases
    if not old_text and not new_text:
        return ""
    if not old_text:
        # Entire content is new
        new_lines = new_text.splitlines(keepends=True)
        diff_lines = [
            f"--- {fromfile}\n",
            f"+++ {tofile}\n",
            f"@@ -0,0 +1,{len(new_lines)} @@\n"
        ]
        diff_lines.extend([f"+{line}" for line in new_lines])
        return "".join(diff_lines)
    if not new_text:
        # Entire content was removed
        old_lines = old_text.splitlines(keepends=True)
        diff_lines = [
            f"--- {fromfile}\n",
            f"+++ {tofile}\n",
            f"@@ -1,{len(old_lines)} +0,0 @@\n"
        ]
        diff_lines.extend([f"-{line}" for line in old_lines])
        return "".join(diff_lines)
    
    # Split texts into lines for diff
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    
    # Check if documents are very large and need special handling
    old_size = len(old_text)
    new_size = len(new_text)
    
    if old_size > MAX_DOCUMENT_SIZE or new_size > MAX_DOCUMENT_SIZE:
        logger.warning(
            f"Large document detected (old: {old_size} bytes, new: {new_size} bytes). "
            "Generating diff with optimized settings."
        )
        # For very large documents, reduce context lines to save memory
        context_lines = min(context_lines, 1)
    
    # Generate unified diff using difflib
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=fromfile,
        tofile=tofile,
        lineterm='',
        n=context_lines
    )
    
    # Convert generator to string
    diff_text = "".join(diff)
    
    # Check if diff is extremely large and truncate if necessary
    if len(diff_text) > MAX_DIFF_SIZE:
        logger.warning(
            f"Diff size ({len(diff_text)} bytes) exceeds maximum ({MAX_DIFF_SIZE} bytes). "
            "Truncating diff with note."
        )
        # Truncate and add note
        truncated = diff_text[:MAX_DIFF_SIZE - 200]  # Leave room for note
        note = f"\n\n[DIFF TRUNCATED: Original diff was {len(diff_text)} bytes, truncated to {len(truncated)} bytes due to size limit]\n"
        diff_text = truncated + note
    
    return diff_text


def generate_html_diff(
    old_text: str,
    new_text: str,
    fromfile: str = "old_version",
    tofile: str = "new_version"
) -> str:
    """
    Generate HTML diff between two text versions (for future use).
    
    Args:
        old_text: Previous version text content
        new_text: New version text content
        fromfile: Label for old version (default: "old_version")
        tofile: Label for new version (default: "new_version")
    
    Returns:
        HTML formatted diff string
    """
    # Split texts into lines
    old_lines = old_text.splitlines(keepends=False)
    new_lines = new_text.splitlines(keepends=False)
    
    # Create HtmlDiff instance
    differ = difflib.HtmlDiff()
    
    # Generate HTML table
    html_diff = differ.make_table(
        old_lines,
        new_lines,
        fromdesc=fromfile,
        todesc=tofile,
        context=True,
        numlines=3
    )
    
    return html_diff

