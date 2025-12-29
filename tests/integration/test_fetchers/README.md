# Integration Test - Germany Sources

## Note on Test Collection

This test file (`test_germany_sources.py`) is excluded from the default pytest run due to a pytest-asyncio collection issue.

## Running This Test

To run this test file specifically:

```bash
# Set environment variables
$env:DATABASE_URL="sqlite+aiosqlite:///:memory:"
$env:JWT_SECRET_KEY="test-secret-key"
$env:ENVIRONMENT="test"

# Run this specific test file
pytest tests/integration/test_fetchers/test_germany_sources.py -v

# Or run with asyncio disabled (if no async tests)
pytest -p no:asyncio tests/integration/test_fetchers/test_germany_sources.py -v
```

## Test Coverage

This test file covers:
- Germany BMI Student Visa fetcher
- Germany BMI Work Visa fetcher  
- Germany Auswärtiges Amt Student Visa fetcher
- Germany Auswärtiges Amt Work Visa fetcher
- Make it in Germany Work Visa fetcher

