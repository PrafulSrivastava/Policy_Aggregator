# Integration Test - Email Sending

## Note on Test Collection

This test file (`test_email_sending.py`) is excluded from the default pytest run due to a pytest-asyncio collection issue.

## Running This Test

To run this test file specifically:

```bash
# Set environment variables
$env:DATABASE_URL="sqlite+aiosqlite:///:memory:"
$env:JWT_SECRET_KEY="test-secret-key"
$env:ENVIRONMENT="test"
$env:RESEND_API_KEY="your-resend-api-key"  # Required for these tests
$env:TEST_EMAIL_RECIPIENT="test@example.com"  # Required for these tests

# Run this specific test file
pytest tests/integration/test_integrations/test_email_sending.py -v
```

## Test Requirements

These tests require:
- Valid `RESEND_API_KEY` environment variable
- Valid `TEST_EMAIL_RECIPIENT` environment variable (test email address)
- Tests will be skipped if `RESEND_API_KEY` is not set

## Test Coverage

This test file covers:
- Email sending via Resend API
- HTML and text email formats
- Email validation
- Error handling (invalid API key, invalid recipient)
- Email service abstraction

