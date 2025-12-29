# Source Fetchers Plugin Architecture

This document describes the plugin-based architecture for source fetchers, which allows adding new policy sources by creating new fetcher modules without modifying core pipeline code.

## Overview

The fetcher system uses a plugin architecture where each source fetcher is a standalone Python module in the `fetchers/` directory. The `FetcherManager` service automatically discovers, loads, and manages these fetcher plugins.

## Architecture

### Components

1. **Base Interface** (`fetchers/base.py`)
   - Defines `FetchResult` data structure for fetch results
   - Defines `SourceFetcher` protocol for fetcher interface
   - Provides standard error types

2. **Fetcher Manager** (`api/services/fetcher_manager.py`)
   - Discovers fetcher modules from `fetchers/` directory
   - Dynamically loads and registers fetchers
   - Matches sources to appropriate fetchers
   - Manages fetcher metadata

3. **Fetcher Plugins** (`fetchers/*.py`)
   - Individual modules for specific government sources
   - Each implements the standard `fetch()` function
   - Follows naming convention: `{country}_{agency}_{visa_type}.py`

## Naming Convention

Fetcher files must follow this naming pattern:

```
{country}_{agency}_{visa_type}.py
```

**Examples:**
- `de_bmi_student.py` - Germany BMI Student visa fetcher
- `de_bmi_workvisa.py` - Germany BMI Work visa fetcher
- `us_dhs_work.py` - US DHS Work visa fetcher

**Rules:**
- `country`: 2-letter ISO country code (lowercase)
- `agency`: Government agency abbreviation (lowercase, underscores allowed)
- `visa_type`: Visa type identifier (lowercase, underscores allowed)
- All parts separated by underscores
- File extension must be `.py`

## Fetcher Interface

All fetchers must implement a `fetch()` function with this signature:

```python
def fetch(url: str, metadata: Dict[str, Any]) -> FetchResult:
    """
    Fetch content from a source URL.
    
    Args:
        url: The URL to fetch content from
        metadata: Additional metadata about the source, including:
            - country: ISO country code (e.g., "DE")
            - visa_type: Type of visa (e.g., "Work", "Student")
            - fetch_type: How to fetch ("html" or "pdf")
            - Any other source-specific configuration
    
    Returns:
        FetchResult containing fetched content or error information
    """
    pass
```

### FetchResult Structure

The `FetchResult` is a Pydantic model with the following fields:

```python
class FetchResult(BaseModel):
    raw_text: str                    # Extracted text content
    content_type: str                # "html", "pdf", or "text"
    fetched_at: datetime             # Timestamp of fetch
    metadata: Dict[str, Any]         # Additional fetch metadata
    success: bool                     # Whether fetch succeeded
    error_message: Optional[str]      # Error message if failed
```

### Source Type Metadata

Fetchers can optionally specify their source type by defining a `SOURCE_TYPE` module-level constant:

```python
SOURCE_TYPE = "html"  # Options: "html", "pdf", "api"
```

This helps the fetcher manager match sources to fetchers based on the source's `fetch_type` field.

## Error Handling

**Critical Rule: Fetchers must NOT raise exceptions.**

Instead, fetchers should return a `FetchResult` with `success=False` and an `error_message` set. This allows the fetcher manager to handle errors gracefully without crashing the pipeline.

### Standard Error Types

Use these error types from `fetchers.base.FetchErrorType`:

- `NETWORK_ERROR` - Network/connection issues
- `PARSE_ERROR` - Content parsing failures
- `AUTHENTICATION_ERROR` - Authentication failures
- `NOT_FOUND_ERROR` - Resource not found (404)
- `TIMEOUT_ERROR` - Request timeout
- `UNKNOWN_ERROR` - Other unexpected errors

### Example Error Handling

```python
from fetchers.base import FetchResult, FetchErrorType

try:
    # Fetch logic here
    result = fetch_content(url)
    return FetchResult(
        raw_text=result,
        content_type="html",
        success=True
    )
except requests.exceptions.Timeout:
    return FetchResult(
        raw_text="",
        content_type="html",
        success=False,
        error_message=f"{FetchErrorType.TIMEOUT_ERROR.value}: Request timed out"
    )
except Exception as e:
    return FetchResult(
        raw_text="",
        content_type="html",
        success=False,
        error_message=f"{FetchErrorType.UNKNOWN_ERROR.value}: {str(e)}"
    )
```

## Creating a New Fetcher

### Step 1: Copy the Template

Copy `fetchers/example_template.py` to create your new fetcher:

```bash
cp fetchers/example_template.py fetchers/de_bmi_student.py
```

### Step 2: Implement the Fetch Function

Replace the template code with your fetcher logic:

```python
"""
Germany BMI Student visa policy fetcher.
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from fetchers.base import FetchResult, FetchErrorType

logger = logging.getLogger(__name__)

SOURCE_TYPE = "html"

def fetch(url: str, metadata: Dict[str, Any]) -> FetchResult:
    """Fetch student visa policy from Germany BMI website."""
    try:
        # Fetch HTML content
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; PolicyAggregator/1.0)'
        })
        response.raise_for_status()
        
        # Parse and extract text
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        raw_text = soup.get_text(separator=' ', strip=True)
        
        # Extract metadata
        page_title = soup.title.string if soup.title else None
        fetch_metadata = {
            'page_title': page_title,
            'content_length': len(raw_text),
            'status_code': response.status_code
        }
        
        return FetchResult(
            raw_text=raw_text,
            content_type="html",
            metadata=fetch_metadata,
            success=True
        )
        
    except requests.exceptions.Timeout:
        return FetchResult(
            raw_text="",
            content_type="html",
            success=False,
            error_message=f"{FetchErrorType.TIMEOUT_ERROR.value}: Request timed out"
        )
    except requests.exceptions.RequestException as e:
        return FetchResult(
            raw_text="",
            content_type="html",
            success=False,
            error_message=f"{FetchErrorType.NETWORK_ERROR.value}: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
        return FetchResult(
            raw_text="",
            content_type="html",
            success=False,
            error_message=f"{FetchErrorType.UNKNOWN_ERROR.value}: {str(e)}"
        )
```

### Step 3: Test Your Fetcher

Test your fetcher manually or write unit tests:

```python
from fetchers.de_bmi_student import fetch

result = fetch("https://example.com/student-visa", {
    "country": "DE",
    "visa_type": "Student",
    "fetch_type": "html"
})

assert result.success is True
assert len(result.raw_text) > 0
```

### Step 4: Register Source in Database

Create a Source record in the database with matching:
- `country`: Must match fetcher country code
- `visa_type`: Must match fetcher visa type
- `fetch_type`: Must match fetcher `SOURCE_TYPE`

The fetcher manager will automatically discover and use your fetcher.

## Fetcher Manager API

### Loading Fetchers

```python
from api.services.fetcher_manager import load_fetchers
from pathlib import Path

# Load all fetchers from default directory
registry = load_fetchers()

# Or specify custom directory
custom_dir = Path("/path/to/fetchers")
registry = load_fetchers(custom_dir)
```

### Getting Fetcher for Source

```python
from api.services.fetcher_manager import get_fetcher_for_source
from api.models.db.source import Source

source = Source(
    country="DE",
    visa_type="Student",
    fetch_type="html",
    # ... other fields
)

fetcher = get_fetcher_for_source(source)
if fetcher:
    result = fetcher(source.url, source.metadata)
```

### Manual Registration

```python
from api.services.fetcher_manager import register_fetcher

def my_custom_fetch(url: str, metadata: dict) -> FetchResult:
    # Custom implementation
    pass

register_fetcher(
    name="custom_fetcher",
    fetch_function=my_custom_fetch,
    metadata={"source_type": "html"}
)
```

## Best Practices

1. **Error Handling**: Always return `FetchResult` with error information, never raise exceptions
2. **Logging**: Use Python's `logging` module for debugging and monitoring
3. **Timeouts**: Always set reasonable timeouts for network requests (30 seconds recommended)
4. **User-Agent**: Include a descriptive User-Agent header in HTTP requests
5. **Metadata**: Include useful metadata in `FetchResult.metadata` (page title, content length, etc.)
6. **Testing**: Test your fetcher with real URLs before deploying
7. **Documentation**: Add docstrings explaining any source-specific requirements

## Troubleshooting

### Fetcher Not Found

**Problem**: `get_fetcher_for_source()` returns `None`

**Solutions**:
- Verify fetcher file follows naming convention: `{country}_{agency}_{visa_type}.py`
- Check that `country` and `visa_type` match exactly (case-insensitive)
- Verify `fetch_type` matches fetcher's `SOURCE_TYPE`
- Ensure `fetch()` function exists in the module
- Check logs for import errors

### Import Errors

**Problem**: Fetcher fails to load with import error

**Solutions**:
- Verify all dependencies are in `requirements.txt`
- Check for syntax errors in fetcher file
- Ensure module doesn't have circular imports
- Test imports manually: `python -c "import fetchers.de_bmi_student"`

### Fetch Failures

**Problem**: Fetcher returns `success=False`

**Solutions**:
- Check `error_message` in `FetchResult` for details
- Verify URL is accessible
- Check network connectivity
- Review source website for changes (HTML structure, authentication, etc.)
- Test with browser to see if source requires JavaScript or special headers

## Example Fetchers

See `fetchers/example_template.py` for a complete template with examples for both HTML and PDF fetching.

## Related Documentation

- [Architecture Components](../architecture/components.md) - System architecture overview
- [Coding Standards](../architecture/coding-standards.md) - Development standards
- [API Specification](../architecture/api-specification.md) - API endpoints



