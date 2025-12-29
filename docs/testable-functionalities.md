# Testable Functionalities

Based on the implemented stories (all marked as "Ready for Review"), here are the functionalities you can test:

## 🎯 Core Infrastructure (Epic 1)

### 1. Health Check & Application Status
**Story:** 1.4 - FastAPI Application Setup and Health Check Endpoint  
**Endpoint:** `GET /health`

**Testable Features:**
- ✅ Application health status
- ✅ Database connection status
- ✅ Timestamp response
- ✅ Error handling when database is unavailable

**Test Files:**
- `tests/integration/test_api/test_health.py`

**Example Test:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "database": "connected", "timestamp": "..."}
```

---

### 2. Authentication System
**Story:** 1.5 - Authentication System  
**Endpoints:**
- `POST /auth/login` - User login with JWT token
- `POST /auth/logout` - Logout (clears session cookie)

**Testable Features:**
- ✅ User login with username/password
- ✅ JWT token generation
- ✅ Password verification (bcrypt)
- ✅ Invalid credentials handling
- ✅ Inactive user handling
- ✅ Session cookie management
- ✅ Last login timestamp update

**Test Files:**
- `tests/integration/test_api/test_auth.py`
- `tests/unit/test_auth/test_password_hashing.py`
- `tests/unit/test_auth/test_jwt_tokens.py`

**Example Test:**
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'

# Response: {"access_token": "...", "token_type": "bearer"}
```

---

### 3. Route Subscription Management
**Story:** 1.6 - Route Subscription API Endpoints  
**Endpoints:**
- `GET /api/routes` - List route subscriptions (paginated)
- `POST /api/routes` - Create route subscription
- `GET /api/routes/{route_id}` - Get specific route subscription
- `DELETE /api/routes/{route_id}` - Delete route subscription

**Testable Features:**
- ✅ Create route subscriptions (origin_country, destination_country, visa_type, email)
- ✅ List route subscriptions with pagination
- ✅ Get route subscription by ID
- ✅ Delete route subscription
- ✅ Duplicate route prevention
- ✅ Validation (country codes, email format)
- ✅ Authentication required for all operations

**Test Files:**
- `tests/integration/test_api/test_routes.py`
- `tests/unit/test_repositories/test_route_subscription_repository.py`

**Example Test:**
```bash
# Create route subscription
curl -X POST http://localhost:8000/api/routes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "origin_country": "IN",
    "destination_country": "DE",
    "visa_type": "Student",
    "email": "user@example.com"
  }'
```

---

### 4. Source Configuration Management
**Story:** 1.7 - Source API Endpoints  
**Endpoints:**
- `GET /api/sources` - List sources (paginated, with filters)
- `POST /api/sources` - Create source
- `GET /api/sources/{source_id}` - Get specific source
- `PUT /api/sources/{source_id}` - Update source
- `DELETE /api/sources/{source_id}` - Delete source
- `POST /api/sources/{source_id}/trigger` - Manually trigger fetch pipeline

**Testable Features:**
- ✅ Create sources (country, visa_type, url, name, fetch_type, check_frequency)
- ✅ List sources with pagination and filters (country, visa_type, is_active)
- ✅ Get source by ID
- ✅ Update source configuration
- ✅ Delete source (with cascade delete)
- ✅ Manual trigger of fetch pipeline
- ✅ Duplicate source prevention
- ✅ Validation (URL format, fetch_type, check_frequency)
- ✅ Source status tracking (last_checked_at, last_change_detected_at)

**Test Files:**
- `tests/integration/test_api/test_sources.py`
- `tests/unit/test_repositories/test_source_repository.py`

**Example Test:**
```bash
# Create source
curl -X POST http://localhost:8000/api/sources \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "DE",
    "visa_type": "Student",
    "url": "https://example.com/policy",
    "name": "Germany Student Visa",
    "fetch_type": "html",
    "check_frequency": "daily"
  }'

# Trigger manual fetch
curl -X POST http://localhost:8000/api/sources/{source_id}/trigger \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 5. Error Handling & Logging
**Story:** 1.8 - Logging and Error Handling Infrastructure  
**Endpoints:** All endpoints with error handling

**Testable Features:**
- ✅ Validation error formatting (400)
- ✅ Authentication error formatting (401)
- ✅ Not found error formatting (404)
- ✅ Conflict error formatting (409)
- ✅ Internal server error handling (500)
- ✅ Database error handling
- ✅ Request logging middleware
- ✅ Error logging with context

**Test Files:**
- `tests/integration/test_api/test_error_handling.py`
- `tests/unit/test_utils/test_logging.py`

---

## 🔄 Data Fetching & Processing (Epic 2)

### 6. Source Fetcher Plugin Architecture
**Story:** 2.1 - Source Fetcher Plugin Architecture  
**Testable Features:**
- ✅ Fetcher discovery and loading
- ✅ Fetcher registry management
- ✅ Fetcher metadata storage
- ✅ Dynamic fetcher selection based on source configuration

**Test Files:**
- `tests/unit/test_services/test_fetcher_manager.py`

---

### 7. HTML Source Fetcher
**Story:** 2.2 - HTML Source Fetcher Implementation  
**Testable Features:**
- ✅ HTML content fetching from URLs
- ✅ Text extraction from HTML (main, article, body tags)
- ✅ Metadata extraction (title, last modified, description)
- ✅ Robots.txt checking
- ✅ Retry logic with exponential backoff
- ✅ Error handling (404, 500, timeout)
- ✅ Redirect handling
- ✅ User-Agent header configuration

**Test Files:**
- `tests/unit/test_fetchers/test_html_fetcher.py`
- `tests/integration/test_fetchers/test_germany_sources.py`

---

### 8. PDF Source Fetcher
**Story:** 2.3 - PDF Source Fetcher Implementation  
**Testable Features:**
- ✅ PDF content fetching from URLs
- ✅ Text extraction from PDF files
- ✅ PDF metadata extraction (page count, title, author)
- ✅ Encrypted PDF handling
- ✅ Error handling (corrupted PDFs, read errors)
- ✅ File-based PDF processing

**Test Files:**
- `tests/unit/test_fetchers/test_pdf_fetcher.py`

---

### 9. Content Normalization Pipeline
**Story:** 2.4 - Normalization Pipeline  
**Testable Features:**
- ✅ Text normalization (whitespace, case, encoding)
- ✅ Boilerplate removal
- ✅ HTML tag removal
- ✅ Special character handling
- ✅ Content length calculation
- ✅ Normalization metadata tracking

**Test Files:**
- `tests/unit/test_services/test_normalizer.py`
- `tests/integration/test_pipeline/test_version_storage.py`

---

### 10. Policy Version Storage
**Story:** 2.5 - Policy Version Storage  
**Testable Features:**
- ✅ Store policy versions with content hash
- ✅ Track fetch timestamps
- ✅ Store normalized content
- ✅ Content hash generation (SHA256)
- ✅ Version retrieval by source
- ✅ Latest version querying

**Test Files:**
- `tests/unit/test_services/test_version_storage.py`
- `tests/unit/test_repositories/test_policy_version_repository.py`
- `tests/integration/test_pipeline/test_version_storage.py`

---

### 11. Change Detection via Hash Comparison
**Story:** 2.6 - Change Detection via Hash Comparison  
**Testable Features:**
- ✅ Hash-based change detection
- ✅ Compare current content hash with previous version
- ✅ First-time detection (no previous version)
- ✅ Change detection result structure
- ✅ Performance optimization (hash comparison before full comparison)

**Test Files:**
- `tests/unit/test_services/test_change_detector.py`
- `tests/integration/test_pipeline/test_change_detection.py`

---

### 12. Text Diff Generation
**Story:** 2.7 - Text Diff Generation  
**Testable Features:**
- ✅ Generate unified diff format
- ✅ Context lines configuration
- ✅ Diff preview generation (truncated)
- ✅ Character limit handling
- ✅ Line limit handling
- ✅ Empty diff handling

**Test Files:**
- `tests/unit/test_services/test_diff_generator.py`
- `tests/integration/test_pipeline/test_diff_generation.py`

---

### 13. Policy Change Record Creation
**Story:** 2.8 - Policy Change Record Creation  
**Testable Features:**
- ✅ Create policy change records
- ✅ Link changes to sources and policy versions
- ✅ Store diff content
- ✅ Change metadata (detected_at, change_type)
- ✅ Change retrieval and querying

**Test Files:**
- `tests/unit/test_services/test_change_storage.py`
- `tests/unit/test_repositories/test_policy_change_repository.py`
- `tests/integration/test_pipeline/test_change_creation.py`

---

### 14. End-to-End Fetch Pipeline
**Story:** 2.9 - End-to-End Fetch Pipeline  
**Testable Features:**
- ✅ Complete pipeline execution (fetch → normalize → detect → store)
- ✅ Pipeline result structure
- ✅ Error handling throughout pipeline
- ✅ Source status updates (last_checked_at)
- ✅ Change detection integration
- ✅ Version storage integration

**Test Files:**
- `tests/unit/test_services/test_fetcher_pipeline.py`
- `tests/integration/test_pipeline/test_end_to_end.py`

---

### 15. Germany Source Fetchers
**Story:** 2.10 - Source Fetchers for India to Germany Route  
**Testable Features:**
- ✅ Germany BMI Student Visa fetcher
- ✅ Germany BMI Work Visa fetcher
- ✅ Germany Auswärtiges Amt Student Visa fetcher
- ✅ Germany Auswärtiges Amt Work Visa fetcher
- ✅ Make it in Germany Work Visa fetcher
- ✅ Fetcher metadata (source, visa_category, route)

**Test Files:**
- `tests/integration/test_fetchers/test_germany_sources.py`

---

## 📧 Alert System (Epic 3)

### 16. Route-to-Source Mapping Logic
**Story:** 3.1 - Route-to-Source Mapping Logic  
**Testable Features:**
- ✅ Map route subscriptions to relevant sources
- ✅ Filter sources by origin_country, destination_country, visa_type
- ✅ Active source filtering
- ✅ Route matching logic

**Test Files:**
- `tests/unit/test_services/test_route_mapper.py`
- `tests/integration/test_services/test_route_mapping.py`

---

### 17. Email Template System
**Story:** 3.2 - Email Template System  
**Testable Features:**
- ✅ HTML email template rendering
- ✅ Plain text email template rendering
- ✅ Template variable substitution
- ✅ Email subject generation
- ✅ Diff preview generation for emails
- ✅ Special character handling in templates

**Test Files:**
- `tests/unit/test_services/test_email_template.py`

---

### 18. Email Sending Service Integration
**Story:** 3.3 - Email Sending Service Integration  
**Testable Features:**
- ✅ Resend API integration
- ✅ Email sending with retry logic
- ✅ Email validation
- ✅ Error handling (network errors, rate limits, validation errors)
- ✅ Email result tracking
- ✅ Rate limit handling

**Test Files:**
- `tests/unit/test_integrations/test_resend.py`
- `tests/integration/test_integrations/test_email_sending.py`

---

### 19. Alert Engine (Change Detection to Email Flow)
**Story:** 3.4 - Alert Engine Change Detection to Email Flow  
**Testable Features:**
- ✅ Change detection triggering
- ✅ Route subscription lookup
- ✅ Email generation for subscribers
- ✅ Batch email sending
- ✅ Email alert record creation
- ✅ Error handling and retry logic

**Test Files:**
- `tests/unit/test_services/test_alert_engine.py`
- `tests/integration/test_services/test_alert_engine.py`

---

### 20. Scheduled Job System
**Story:** 3.5 - Scheduled Job System  
**Testable Features:**
- ✅ Daily fetch job execution
- ✅ Source filtering by check_frequency
- ✅ Batch processing of sources
- ✅ Job result tracking
- ✅ Error aggregation
- ✅ Success/failure reporting

**Test Files:**
- `tests/unit/test_services/test_scheduler.py`
- `tests/integration/test_jobs/test_daily_fetch_job.py`

**Example Test:**
```bash
# Trigger daily fetch job via API
curl -X POST http://localhost:8000/api/jobs/daily-fetch \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 21. Error Notification System
**Story:** 3.7 - Error Notification System  
**Testable Features:**
- ✅ Source error tracking (consecutive_fetch_failures)
- ✅ Email delivery error tracking (consecutive_email_failures)
- ✅ Error message storage
- ✅ Error threshold detection
- ✅ Error notification emails

**Test Files:**
- `tests/unit/test_services/test_error_tracker.py`
- `tests/integration/test_services/test_error_notification.py`

---

### 22. End-to-End Alert System Test
**Story:** 3.8 - End-to-End Alert System Test  
**Testable Features:**
- ✅ Complete flow: Source fetch → Change detection → Email alert
- ✅ Multiple route subscriptions
- ✅ Email delivery verification
- ✅ Change record creation verification
- ✅ Integration testing of all components

**Test Files:**
- `tests/integration/test_e2e/test_alert_system.py`

---

## 🧪 Testing Commands

### Run All Tests
```bash
# Set environment variables
$env:DATABASE_URL="sqlite+aiosqlite:///:memory:"
$env:JWT_SECRET_KEY="test-secret-key"
$env:ENVIRONMENT="test"

# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov=fetchers --cov-report=html

# Run specific test category
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/integration/test_api/    # API tests only
```

### Run Specific Test Suites
```bash
# Authentication tests
pytest tests/unit/test_auth/ tests/integration/test_api/test_auth.py

# Fetcher tests
pytest tests/unit/test_fetchers/ tests/integration/test_fetchers/

# Pipeline tests
pytest tests/integration/test_pipeline/

# Alert system tests
pytest tests/unit/test_services/test_alert_engine.py tests/integration/test_e2e/
```

### Manual API Testing
```bash
# Start the server
uvicorn api.main:app --reload

# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'

# Use token for authenticated requests
TOKEN="your_token_here"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/routes
```

---

## 📊 Test Coverage Summary

Based on the test files, you have comprehensive coverage for:

- ✅ **22 Core Functionalities** across 3 epics
- ✅ **Unit Tests**: 13 service test files, 5 repository test files, 2 fetcher test files
- ✅ **Integration Tests**: API endpoints, pipeline, jobs, e2e alert system
- ✅ **Total Test Files**: 30+ test files covering all major components

---

## 🚀 Next Steps for Testing

1. **Set up PostgreSQL** (see `docs/setup-postgres.md`)
2. **Run database migrations**: `alembic upgrade head`
3. **Create admin user**: `python scripts/create_admin_user.py admin yourpassword`
4. **Start the server**: `uvicorn api.main:app --reload`
5. **Run tests**: `pytest`
6. **Test API endpoints**: Use the examples above or visit `http://localhost:8000/docs` for interactive API documentation

---

## 📝 Notes

- All stories are marked as "Ready for Review"
- Test files exist for all major functionalities
- Some integration tests may require database setup
- Email sending tests require Resend API key (optional for development)
- Manual trigger endpoint allows testing fetch pipeline without waiting for scheduled jobs

