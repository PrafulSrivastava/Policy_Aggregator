# Content Normalization

This document describes the content normalization pipeline that prepares fetched text for stable diff comparison and change detection.

## Overview

The normalization pipeline processes raw text content from fetchers to ensure consistent change detection. It removes formatting differences that would cause false positives while preserving meaningful content structure.

## Purpose

Normalization enables:
- **Stable change detection**: Same content produces same normalized output regardless of formatting
- **Reduced false positives**: Formatting changes (whitespace, line breaks) don't trigger change alerts
- **Consistent hashing**: Normalized content produces consistent SHA256 hashes for comparison
- **Better diffs**: Cleaner diffs focus on actual content changes, not formatting

## Normalization Steps

The normalization process applies the following steps in order:

### 1. Line Break Normalization

**Purpose**: Ensure consistent line endings across different operating systems.

**Process**:
- Converts Windows line endings (`\r\n`) to Unix (`\n`)
- Converts Mac line endings (`\r`) to Unix (`\n`)
- Unix line endings (`\n`) remain unchanged

**Example**:
```
Before: "Line 1\r\nLine 2\rLine 3\nLine 4"
After:  "Line 1\nLine 2\nLine 3\nLine 4"
```

**Rationale**: Different operating systems use different line endings. Normalizing to Unix-style ensures consistent comparison regardless of source.

### 2. Boilerplate Removal

**Purpose**: Remove headers, footers, navigation, and other non-content elements that may change without actual content changes.

**Common Patterns Removed**:
- Copyright notices: `Copyright © 2024...`
- "All rights reserved" notices
- "Last updated" timestamps
- Page numbers: `Page 1 of 5`
- Navigation menu items: `Home | About | Contact`
- Contact information headers
- Legal disclaimers

**Example**:
```
Before: "Copyright © 2024 Government Agency\n\nMain content here\n\nLast updated: 2024-01-27"
After:  "Main content here"
```

**Rationale**: These elements often change (e.g., update timestamps) without actual policy content changes, causing false positives.

### 3. Whitespace Normalization

**Purpose**: Normalize whitespace while preserving structure.

**Process**:
- Strips leading and trailing whitespace from each line
- Normalizes multiple spaces/tabs to single space
- Preserves line breaks and paragraph structure

**Example**:
```
Before: "  Hello    World  \n  Test   Content  "
After:  "Hello World\nTest Content"
```

**Rationale**: Whitespace differences (extra spaces, tabs) don't represent content changes and should be normalized.

### 4. Structure Preservation

**Purpose**: Preserve meaningful content structure (paragraphs, sections).

**Process**:
- Normalizes 3+ consecutive newlines to double newline (paragraph break)
- Removes trailing newlines at start and end
- Preserves paragraph breaks (double newlines)

**Example**:
```
Before: "Paragraph 1\n\n\n\n\nParagraph 2"
After:  "Paragraph 1\n\nParagraph 2"
```

**Rationale**: Paragraph structure is meaningful and should be preserved, but excessive blank lines are normalized.

### 5. Final Trim

**Purpose**: Remove any remaining leading/trailing whitespace.

**Process**:
- Strips whitespace from the beginning and end of the entire text

## Configuration

### Default Rules

The normalization pipeline includes default boilerplate removal patterns that work for most government sources. These patterns are defined in `api/services/normalization_rules.py`.

### Source-Specific Rules

You can configure custom normalization rules per source via the source metadata:

```python
source_metadata = {
    'normalization_rules': [
        {
            'pattern': r'^REMOVE THIS.*?$',  # Regex pattern
            'replacement': '',                # Replacement (empty = remove)
            'flags': 0,                       # Regex flags (re.IGNORECASE, etc.)
            'description': 'Custom removal rule'
        }
    ]
}

normalized_text = normalize(raw_text, source_metadata=source_metadata)
```

### Disabling Boilerplate Removal

You can disable boilerplate removal if needed:

```python
normalized_text = normalize(raw_text, remove_boilerplate_enabled=False)
```

## Usage

### Basic Usage

```python
from api.services.normalizer import normalize

# Normalize raw text from fetcher
raw_text = fetcher_result.raw_text
normalized_text = normalize(raw_text)

# Use normalized text for hashing and change detection
content_hash = hashlib.sha256(normalized_text.encode()).hexdigest()
```

### With Source Metadata

```python
from api.services.normalizer import normalize

source_metadata = {
    'country': 'DE',
    'visa_type': 'Student',
    'normalization_rules': [
        {
            'pattern': r'^Custom pattern.*?$',
            'replacement': '',
            'description': 'Remove custom pattern'
        }
    ]
}

normalized_text = normalize(raw_text, source_metadata=source_metadata)
```

## Examples

### Example 1: Whitespace Normalization

**Before**:
```
  Policy Title    

  Section 1: Introduction
    This is the first paragraph.    It has extra spaces.
    
    This is the second paragraph.
```

**After**:
```
Policy Title

Section 1: Introduction
This is the first paragraph. It has extra spaces.

This is the second paragraph.
```

### Example 2: Line Break Normalization

**Before** (Windows line endings):
```
Line 1\r\n
Line 2\r\n
Line 3\r\n
```

**After** (Unix line endings):
```
Line 1\n
Line 2\n
Line 3\n
```

### Example 3: Boilerplate Removal

**Before**:
```
Copyright © 2024 Government Agency
All rights reserved

Main Policy Content Here

Last updated: 2024-01-27
Contact: info@government.gov
```

**After**:
```
Main Policy Content Here
```

### Example 4: Complete Normalization

**Before**:
```
  Policy Document    \r\n\r\n
  Copyright © 2024  \r\n
  \r\n
  Section 1: Introduction\r\n
    This is important content.    It has formatting issues.\r\n
  \r\n
  Section 2: Details\r\n
    More content here.\r\n
  \r\n
  Last updated: 2024-01-27\r\n
```

**After**:
```
Section 1: Introduction
This is important content. It has formatting issues.

Section 2: Details
More content here.
```

## Performance

The normalization pipeline is optimized for performance:

- **Efficient string operations**: Uses compiled regex patterns
- **Single-pass where possible**: Minimizes multiple passes over text
- **Handles large documents**: Tested with 100KB+ documents, completes in < 1 second
- **Deterministic**: Same input always produces same output

### Performance Benchmarks

- **Small document** (< 10KB): < 10ms
- **Medium document** (10-100KB): < 100ms
- **Large document** (100KB-1MB): < 1 second
- **Very large document** (> 1MB): < 5 seconds

## Design Principles

### What Normalization Does

✅ **Normalizes formatting**: Whitespace, line breaks, boilerplate
✅ **Preserves structure**: Paragraphs, sections, meaningful breaks
✅ **Deterministic**: Same input → same output
✅ **Configurable**: Source-specific rules supported
✅ **Performance-focused**: Efficient for large documents

### What Normalization Does NOT Do

❌ **Semantic parsing**: Does not interpret meaning
❌ **Content modification**: Does not change actual content
❌ **Language-specific**: Does not perform language-specific processing
❌ **Content extraction**: Does not extract specific fields (handled by fetchers)

## Testing

The normalization pipeline includes comprehensive unit tests covering:

- Whitespace normalization (leading/trailing, multiple spaces, tabs)
- Line break normalization (Windows, Mac, Unix)
- Boilerplate removal (headers, footers, navigation)
- Structure preservation (paragraphs, sections)
- Edge cases (empty text, very large text)
- Performance (large documents)
- Deterministic output (same input → same output)

See `tests/unit/test_services/test_normalizer.py` for test examples.

## Troubleshooting

### Normalization Removes Important Content

**Problem**: Normalization removes content that should be preserved.

**Solution**: 
1. Check if a default boilerplate pattern is matching your content
2. Disable boilerplate removal: `normalize(text, remove_boilerplate_enabled=False)`
3. Add a custom rule to exclude your content from removal

### Normalization Too Slow

**Problem**: Normalization takes too long for large documents.

**Solution**:
1. Check document size - normalization should handle 100KB+ documents efficiently
2. Review custom rules - complex regex patterns can slow down processing
3. Consider processing in chunks if documents are extremely large (> 10MB)

### Inconsistent Normalization

**Problem**: Same input produces different output.

**Solution**:
- Normalization is deterministic - if you see inconsistencies, check:
  1. Input text is actually the same (may have hidden characters)
  2. Source metadata is the same (custom rules affect output)
  3. Normalization function parameters are the same

## Related Documentation

- [Architecture Components](../architecture/components.md) - System architecture overview
- [Coding Standards](../architecture/coding-standards.md) - Development standards
- [Fetcher Documentation](./fetchers/README.md) - Source fetcher documentation



