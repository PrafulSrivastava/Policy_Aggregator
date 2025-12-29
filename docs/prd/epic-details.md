# Epic Details

### Epic 1: Foundation & Core Infrastructure

**Expanded Goal:** Establish the foundational infrastructure for the Policy Aggregator MVP. This includes project setup with proper tooling (Git, CI/CD basics), database schema design and implementation for all core entities (Source, PolicyVersion, PolicyChange, RouteSubscription), basic REST API with authentication, and RouteSubscription API endpoints to enable route management. The epic delivers a deployable application with a health check endpoint, working data persistence layer, and API infrastructure that all subsequent epics will build upon. This foundation ensures versioning, hashing, and source attribution are implemented correctly from day one, as these cannot be recovered if done wrong.

#### Story 1.1: Project Setup and Repository Structure

As a **admin/developer**,  
I want **a properly structured monorepo with development tooling**,  
so that **I have a solid foundation for building the application with clear organization and development workflows**.

**Acceptance Criteria:**

1. Repository initialized with Git, proper `.gitignore` for Python projects
2. Directory structure created: `fetchers/`, `api/`, `admin-ui/`, `scripts/`, `tests/`, `docs/`
3. Python virtual environment setup documented
4. Basic `requirements.txt` with core dependencies (FastAPI, SQLAlchemy, etc.)
5. README.md with project overview, setup instructions, and development guidelines
6. Basic CI/CD configuration (GitHub Actions) for running tests (placeholder for now)
7. Environment variable template file (`.env.example`) with required variables documented

#### Story 1.2: Database Schema and Migration System

As a **developer**,  
I want **PostgreSQL database schema with migration system**,  
so that **I can version database changes and ensure data integrity for all core entities**.

**Acceptance Criteria:**

1. PostgreSQL database connection configured (using environment variables)
2. Migration system set up (Alembic or similar)
3. Core tables created with proper schema:
   - `Source`: id, country, visa_type, url, fetch_type, check_frequency, created_at, updated_at
   - `PolicyVersion`: id, source_id, content_hash (SHA256), raw_text, fetched_at, created_at
   - `PolicyChange`: id, source_id, old_hash, new_hash, diff (text), detected_at, created_at
   - `RouteSubscription`: id, org_id, origin, destination, visa_type, email, created_at, updated_at
4. Foreign key relationships properly defined (Source → PolicyVersion, Source → PolicyChange)
5. Indexes created on: source_id, content_hash, fetched_at, detected_at, (origin, destination, visa_type)
6. JSONB fields used where appropriate (source metadata, route configs)
7. Migration scripts tested and can be run up/down successfully
8. Database connection pooling configured

#### Story 1.3: Core Data Model and Business Logic Layer

As a **developer**,  
I want **Python models and business logic for core entities**,  
so that **I have a clean abstraction layer for database operations and can implement versioning and hashing logic**.

**Acceptance Criteria:**

1. SQLAlchemy models created for: Source, PolicyVersion, PolicyChange, RouteSubscription
2. Repository/service layer with methods for:
   - Source CRUD operations
   - PolicyVersion creation and retrieval (by source_id, by hash)
   - PolicyChange creation and retrieval (by source_id, by route)
   - RouteSubscription CRUD operations
3. Hashing utility function: SHA256 hash generation for policy content
4. Versioning logic: PolicyVersion records are immutable (never updated, only new versions created)
5. Helper functions for: finding latest PolicyVersion for a source, comparing hashes
6. Unit tests for models and business logic (hashing, versioning)
7. Data validation: ensure required fields, proper data types, constraints

#### Story 1.4: FastAPI Application Setup and Health Check Endpoint

As a **developer**,  
I want **FastAPI application with basic structure and health check endpoint**,  
so that **I have a deployable API foundation and can verify the application is running**.

**Acceptance Criteria:**

1. FastAPI application initialized with proper project structure
2. Health check endpoint (`GET /health`) returns:
   - Application status: "healthy"
   - Database connection status: "connected" or "disconnected"
   - Timestamp
3. Basic error handling middleware configured
4. CORS configured (if needed for admin UI)
5. Request logging middleware configured
6. OpenAPI/Swagger documentation accessible at `/docs`
7. Application can be run locally and health check responds correctly
8. Environment-based configuration (development, production)

#### Story 1.5: Authentication System

As an **admin user**,  
I want **simple password-based authentication**,  
so that **I can securely access the admin interface and API endpoints**.

**Acceptance Criteria:**

1. User model/table for admin users (username, hashed_password, created_at)
2. Password hashing using secure method (bcrypt or similar)
3. Login endpoint (`POST /auth/login`) that:
   - Accepts username and password
   - Validates credentials
   - Returns session token or sets session cookie
4. Authentication middleware/dependency for protecting routes
5. Logout functionality
6. Session management (JWT tokens or server-side sessions)
7. At least one admin user can be created (via script or migration)
8. Protected endpoints require authentication (test with health check remaining public)

#### Story 1.6: RouteSubscription API Endpoints

As a **developer/admin**,  
I want **REST API endpoints for managing route subscriptions**,  
so that **I can create and manage routes programmatically before the admin UI is built**.

**Acceptance Criteria:**

1. `GET /api/routes` - List all route subscriptions (with pagination)
2. `POST /api/routes` - Create new route subscription:
   - Request body: origin, destination, visa_type, email
   - Validation: required fields, valid country codes, valid email
   - Returns created route subscription
3. `GET /api/routes/{id}` - Get specific route subscription
4. `DELETE /api/routes/{id}` - Delete route subscription
5. All endpoints require authentication
6. Proper HTTP status codes (200, 201, 404, 400, 401)
7. Error responses include meaningful error messages
8. API documented in OpenAPI/Swagger
9. Integration tests for all endpoints

#### Story 1.7: Source API Endpoints

As a **developer/admin**,  
I want **REST API endpoints for managing sources**,  
so that **I can configure and manage policy sources programmatically**.

**Acceptance Criteria:**

1. `GET /api/sources` - List all sources (with pagination, filtering by country/visa_type)
2. `POST /api/sources` - Create new source:
   - Request body: country, visa_type, url, fetch_type, check_frequency
   - Validation: required fields, valid URL, valid fetch_type
   - Returns created source
3. `GET /api/sources/{id}` - Get specific source with metadata
4. `PUT /api/sources/{id}` - Update source configuration
5. `DELETE /api/sources/{id}` - Delete source (with cascade handling)
6. All endpoints require authentication
7. Proper HTTP status codes and error handling
8. Integration tests for all endpoints

#### Story 1.8: Logging and Error Handling Infrastructure

As a **developer**,  
I want **structured logging and error handling**,  
so that **I can debug issues and monitor application health throughout development and production**.

**Acceptance Criteria:**

1. Python `logging` module configured with appropriate log levels
2. Logging format includes: timestamp, level, module, message
3. Logs written to stdout (for hosting platform capture) and optionally to files
4. Error handling middleware catches unhandled exceptions
5. Error responses include: error message, error code, timestamp (no stack traces in production)
6. Critical operations logged (database connections, authentication attempts, API errors)
7. Log rotation configured (if file logging used)
8. Different log levels for development vs production environments

---

### Epic 2: Source Fetching & Change Detection Pipeline

**Expanded Goal:** Build the core monitoring engine that makes the product valuable. This epic implements plugin-based source fetchers that can scrape HTML and extract text from PDFs, a normalization pipeline that prepares content for stable diff comparison, and deterministic change detection using SHA256 hashing and text diffs. The epic delivers the ability to fetch policy sources, detect when content changes, and store versioned policy documents with full audit trail. This is the heart of the product - without this capability, alerts and automation have nothing to work with. The plugin architecture ensures adding new sources is trivial and doesn't require core code changes.

#### Story 2.1: Source Fetcher Plugin Architecture

As a **developer**,  
I want **a plugin-based architecture for source fetchers**,  
so that **I can add new sources by creating new files without modifying core pipeline code**.

**Acceptance Criteria:**

1. Base fetcher interface/abstract class defined with standard method signature:
   - Input: source URL and metadata
   - Output: raw text content and fetch metadata (timestamp, content_type, etc.)
2. Fetcher registry system that can discover and load fetcher modules from `fetchers/` directory
3. Fetcher naming convention: `{country}_{agency}_{visa_type}.py` (e.g., `de_bmi_workvisa.py`)
4. Each fetcher is a standalone Python module with a `fetch()` function
5. Error handling: fetchers return success/failure status with error messages
6. Fetcher metadata: each fetcher can specify its source type (HTML, PDF, API)
7. Unit tests for fetcher registry and loading mechanism
8. Documentation: example fetcher template and guidelines for creating new fetchers

#### Story 2.2: HTML Source Fetcher Implementation

As a **developer**,  
I want **HTML scraping capability using Requests and BeautifulSoup**,  
so that **I can fetch policy content from government websites**.

**Acceptance Criteria:**

1. HTML fetcher module that uses `requests` library to fetch web pages
2. BeautifulSoup integration for parsing HTML and extracting text content
3. Handles common HTML structures: main content areas, article tags, div containers
4. Strips HTML tags and returns clean text content
5. Handles HTTP errors gracefully (404, 500, timeout) with retry logic
6. Respects `robots.txt` (checks before fetching, logs if blocked)
7. User-Agent header configured appropriately
8. Handles redirects correctly
9. Extracts and preserves important metadata: page title, last modified date (if available)
10. Unit tests with mock HTTP responses
11. At least one working HTML fetcher for a real Germany immigration source (test source)

#### Story 2.3: PDF Source Fetcher Implementation

As a **developer**,  
I want **PDF text extraction capability**,  
so that **I can extract policy content from PDF documents**.

**Acceptance Criteria:**

1. PDF fetcher module that can extract text from PDF files
2. Uses `pdftotext` (via subprocess) or `PyPDF2`/`pdfplumber` library
3. Handles PDFs fetched from URLs (download PDF, extract text, clean up temp file)
4. Handles local PDF files (for testing)
5. Extracts text while preserving basic structure (paragraphs, line breaks)
6. Handles encrypted/protected PDFs gracefully (returns error)
7. Handles corrupted or invalid PDFs gracefully (returns error)
8. Extracts metadata: page count, creation date (if available)
9. Unit tests with sample PDF files
10. At least one working PDF fetcher for a real Germany immigration source (test source)

#### Story 2.4: Normalization Pipeline

As a **developer**,  
I want **a normalization pipeline that prepares content for stable diff comparison**,  
so that **I can detect real changes without false positives from formatting differences**.

**Acceptance Criteria:**

1. Normalization function that processes raw fetched text:
   - Strips leading/trailing whitespace from each line
   - Normalizes multiple spaces to single space
   - Normalizes line breaks (handles Windows/Unix/Mac line endings)
   - Removes common boilerplate (headers, footers, navigation if identifiable)
2. Configurable normalization rules (can be adjusted per source if needed)
3. Preserves meaningful content structure (paragraphs, sections)
4. Does NOT perform semantic parsing or interpretation
5. Unit tests with before/after examples showing normalization
6. Test cases: whitespace normalization, line break normalization, boilerplate removal
7. Documentation of normalization rules and rationale
8. Performance: normalization completes quickly even for large documents

#### Story 2.5: Policy Version Storage

As a **developer**,  
I want **automatic storage of fetched policy content as versioned documents**,  
so that **I have a complete audit trail of all policy versions over time**.

**Acceptance Criteria:**

1. After successful fetch and normalization, create PolicyVersion record:
   - source_id (foreign key)
   - content_hash (SHA256 of normalized content)
   - raw_text (normalized text content)
   - fetched_at (timestamp)
2. PolicyVersion records are immutable (never updated, only new versions created)
3. If same hash already exists for a source, do not create duplicate (idempotent)
4. Store full text content (not just hash) for diff generation later
5. Database indexes on source_id and fetched_at for efficient queries
6. Helper function to retrieve latest PolicyVersion for a source
7. Helper function to retrieve PolicyVersion by hash
8. Unit tests for version storage logic
9. Integration test: fetch same source twice, verify only one version if unchanged

#### Story 2.6: Change Detection via Hash Comparison

As a **developer**,  
I want **deterministic change detection using SHA256 hash comparison**,  
so that **I can quickly identify when policy content has changed**.

**Acceptance Criteria:**

1. After storing new PolicyVersion, compare hash with previous version's hash
2. If hashes match: no change detected, log and continue
3. If hashes differ: change detected, trigger diff generation
4. Hash comparison is fast and deterministic (same content always produces same hash)
5. Handles edge cases:
   - First fetch for a source (no previous version to compare)
   - Source fetch fails (no version stored, no comparison)
6. Logs change detection results (changed/unchanged) for auditability
7. Unit tests for hash comparison logic
8. Integration test: fetch source, modify content slightly, fetch again, verify change detected

#### Story 2.7: Text Diff Generation

As a **developer**,  
I want **text diff generation using Python difflib**,  
so that **I can show exactly what changed between policy versions**.

**Acceptance Criteria:**

1. When change detected, generate diff using `difflib.unified_diff()` or `difflib.HtmlDiff()`
2. Diff compares: previous PolicyVersion.raw_text vs new PolicyVersion.raw_text
3. Diff output stored as text in PolicyChange.diff field
4. Diff includes context lines (configurable, default 3 lines)
5. Diff format is human-readable (unified diff or HTML diff)
6. Handles large documents efficiently (no memory issues)
7. Unit tests with sample text changes:
   - Added text
   - Removed text
   - Modified text
   - Multiple changes
8. Integration test: create PolicyChange record with diff when change detected
9. Helper function to retrieve PolicyChange with formatted diff for display

#### Story 2.8: PolicyChange Record Creation

As a **developer**,  
I want **automatic creation of PolicyChange records when changes are detected**,  
so that **I have a complete history of all policy changes with timestamps and diffs**.

**Acceptance Criteria:**

1. When change detected (hash differs), create PolicyChange record:
   - source_id (foreign key)
   - old_hash (previous PolicyVersion hash)
   - new_hash (current PolicyVersion hash)
   - diff (text diff from difflib)
   - detected_at (timestamp)
2. PolicyChange records are immutable (never updated)
3. Link PolicyChange to both old and new PolicyVersions (via hashes)
4. Database index on detected_at for efficient chronological queries
5. Database index on source_id for efficient source-based queries
6. Helper functions:
   - Get all changes for a source
   - Get changes within date range
   - Get latest change for a source
7. Unit tests for PolicyChange creation
8. Integration test: full flow - fetch, change detected, PolicyChange created with diff

#### Story 2.9: End-to-End Fetch Pipeline

As a **developer**,  
I want **a complete fetch pipeline that orchestrates all steps**,  
so that **I can fetch a source, normalize, detect changes, and store results in one operation**.

**Acceptance Criteria:**

1. Main pipeline function: `fetch_and_process_source(source_id)`
2. Pipeline steps executed in order:
   - Load source configuration from database
   - Select appropriate fetcher based on source.fetch_type
   - Execute fetcher to get raw content
   - Normalize content
   - Generate hash
   - Compare with previous version
   - Store PolicyVersion
   - If changed: generate diff, create PolicyChange
3. Error handling: if any step fails, log error and continue with next source (graceful degradation)
4. Retry logic: transient failures retried 2-3 times with exponential backoff
5. Logging at each step for debugging and auditability
6. Returns summary: success/failure, change detected yes/no, error messages
7. Integration test: full pipeline with real source (or mock)
8. Unit tests for each pipeline step
9. Can be called manually via API endpoint for testing

#### Story 2.10: Source Fetchers for India → Germany Route

As a **developer**,  
I want **working source fetchers for 3-5 official Germany immigration sources**,  
so that **I can monitor real policy sources for the MVP route**.

**Acceptance Criteria:**

1. Implement 3-5 source fetchers for India → Germany route:
   - At least one Student visa source
   - At least one Work visa source
   - Mix of HTML and PDF sources if available
2. Each fetcher tested with real source URLs
3. Fetchers handle actual source structure (may require source-specific parsing)
4. All fetchers follow plugin architecture (separate files, standard interface)
5. Source configurations added to database (via API or migration)
6. Documentation: list of sources, URLs, what each monitors
7. Integration test: run all fetchers, verify they return content
8. Manual verification: fetched content matches source (spot check)

---

### Epic 3: Alert System & Automation

**Expanded Goal:** Transform the monitoring capability into a proactive service that triggers payment. This epic implements the alert engine that maps route subscriptions to sources, email notification system with proper templates, and automated scheduling that runs the full pipeline daily. The epic delivers the core value proposition: users receive email alerts when policy changes are detected for their subscribed routes, with diffs and source attribution. This is what makes the product sellable - without alerts, it's just a data collection tool. The automation ensures the system runs reliably without manual intervention, creating the "watchdog" effect that builds trust.

#### Story 3.1: Route-to-Source Mapping Logic

As a **developer**,  
I want **logic that maps route subscriptions to relevant sources**,  
so that **I can determine which sources to monitor for each route subscription**.

**Acceptance Criteria:**

1. Mapping function: given a RouteSubscription (origin, destination, visa_type), return list of relevant Sources
2. Mapping logic: match sources by destination country and visa_type
3. Sources can be associated with multiple routes (many-to-many relationship)
4. Helper function: get all routes affected by a source change
5. Helper function: get all sources for a route subscription
6. Edge cases handled:
   - Route with no matching sources (log warning)
   - Source with no matching routes (still monitored, but no alerts sent)
7. Unit tests for mapping logic
8. Integration test: create routes and sources, verify correct mappings

#### Story 3.2: Email Template System

As a **developer**,  
I want **email templates for policy change alerts**,  
so that **users receive clear, actionable notifications with all necessary information**.

**Acceptance Criteria:**

1. Email template with placeholders for:
   - Route (origin → destination, visa_type)
   - Source name and URL
   - Detected timestamp
   - Diff preview (first 500 characters or first 20 lines)
   - Link to full diff (admin UI URL)
2. Template is HTML format (with plain text fallback)
3. Email subject line: "Policy Change Detected: [Route] - [Source Name]"
4. Email includes clear call-to-action: "View Full Diff" button/link
5. Template includes source attribution prominently (builds trust)
6. Template includes disclaimer: "This is information, not legal advice"
7. Template is configurable (can be updated without code changes)
8. Unit tests: template rendering with sample data
9. Manual test: render template and verify formatting

#### Story 3.3: Email Sending Service Integration

As a **developer**,  
I want **integration with transactional email service (Resend/SES/Mailgun)**,  
so that **I can reliably send email alerts to users**.

**Acceptance Criteria:**

1. Email service client configured (API key from environment variables)
2. Send email function that:
   - Accepts: recipient email, subject, HTML body, plain text body
   - Returns: success/failure status, message ID
3. Error handling: network failures, API errors, invalid emails
4. Retry logic: transient failures retried 2-3 times
5. Logging: all email sends logged (success/failure, recipient, timestamp)
6. Rate limiting: respect email service limits
7. Unit tests with mock email service
8. Integration test: send test email to real address, verify delivery
9. Email service provider can be switched (abstraction layer)

#### Story 3.4: Alert Engine - Change Detection to Email Flow

As a **developer**,  
I want **an alert engine that sends emails when policy changes are detected**,  
so that **users are proactively notified of relevant changes**.

**Acceptance Criteria:**

1. Alert function: `send_alerts_for_change(policy_change_id)`
2. Flow:
   - Get PolicyChange record
   - Get Source from PolicyChange
   - Find all RouteSubscriptions that match this source (via mapping logic)
   - For each route subscription, send email alert
3. Email includes: route info, source info, timestamp, diff preview, link to full diff
4. Each route subscription gets one email (even if multiple sources changed)
5. If no routes match the source, log but don't send emails
6. Error handling: if email fails for one route, continue with others
7. Logging: all alert sends logged (route, email, success/failure)
8. Integration test: create change, verify emails sent to matching routes
9. Unit tests for alert logic

#### Story 3.5: Scheduled Job System

As a **developer**,  
I want **a scheduled job system that runs the fetch pipeline daily**,  
so that **the system monitors sources automatically without manual intervention**.

**Acceptance Criteria:**

1. Scheduled job function: `run_daily_fetch_job()`
2. Job orchestrates:
   - Get all active sources from database
   - For each source, run fetch pipeline
   - If change detected, trigger alert engine
3. Job handles errors gracefully: one source failure doesn't stop others
4. Job logs start/end time, sources processed, changes detected, errors
5. Job can be triggered manually via API endpoint for testing
6. Job respects source.check_frequency (daily for MVP, but extensible)
7. Integration test: run job with test sources, verify full flow
8. Unit tests for job orchestration logic

#### Story 3.6: GitHub Actions Cron Configuration

As a **developer**,  
I want **GitHub Actions workflow that runs the daily fetch job on a schedule**,  
so that **the system runs automatically in production without a dedicated server**.

**Acceptance Criteria:**

1. GitHub Actions workflow file (`.github/workflows/daily-fetch.yml`)
2. Workflow scheduled to run daily (configurable time, e.g., 2 AM UTC)
3. Workflow:
   - Checks out code
   - Sets up Python environment
   - Installs dependencies
   - Sets environment variables (from GitHub Secrets)
   - Runs daily fetch job script
4. Workflow logs output and errors
5. Workflow sends notification on failure (email or Slack, if configured)
6. Workflow can be triggered manually from GitHub UI
7. Documentation: how to set up secrets, how to modify schedule
8. Test: trigger workflow manually, verify job runs successfully

#### Story 3.7: Error Notification System

As a **developer**,  
I want **error notifications sent to admin when persistent failures occur**,  
so that **I can quickly identify and fix issues with source fetching or email delivery**.

**Acceptance Criteria:**

1. Error tracking: track failures per source (consecutive failure count)
2. Threshold: if source fails 3+ times consecutively, send admin notification
3. Admin notification email includes:
   - Source name and URL
   - Error message
   - Failure count
   - Last successful fetch timestamp
4. Error notifications sent to admin email (from environment variable)
5. Error tracking resets when source successfully fetches
6. Different error types tracked separately (fetch errors vs email errors)
7. Unit tests for error tracking logic
8. Integration test: simulate failures, verify admin notification sent

#### Story 3.8: End-to-End Alert System Test

As a **developer**,  
I want **comprehensive testing of the complete alert system**,  
so that **I can verify the entire flow from source change to email delivery works correctly**.

**Acceptance Criteria:**

1. End-to-end test scenario:
   - Create route subscription
   - Create source
   - Manually trigger fetch (simulate change)
   - Verify PolicyChange created
   - Verify email sent to route subscription email
   - Verify email content is correct
2. Test with multiple routes matching one source (verify all get emails)
3. Test with route that has no matching sources (verify no false alerts)
4. Test error scenarios: email service failure, source fetch failure
5. Test scheduled job runs successfully
6. Manual verification: run full pipeline, check email inbox
7. Documentation: how to test alert system manually

---

### Epic 4: Admin Interface

**Expanded Goal:** Create the user-facing admin interface that enables route and source management, change history viewing, and system monitoring. While email is the primary user experience, the admin UI is essential for initial setup, verification, and trust-building. Users need to see what sources are monitored, when they were last checked, and view change history with diffs. The interface should be simple, functional, and professional - "boring is good" applies here too. The UI enables users to verify the system is working, configure their routes, and manually trigger fetches for testing.

#### Story 4.1: Admin UI Foundation and Authentication

As an **admin user**,  
I want **a web-based admin interface with authentication**,  
so that **I can securely access the management interface**.

**Acceptance Criteria:**

1. Admin UI built with template-based framework (Jinja2 with FastAPI)
2. Login page with username/password form
3. Login integrates with existing authentication system (from Epic 1)
4. Session management: user stays logged in (session cookie or JWT)
5. Logout functionality
6. Protected routes: all admin pages require authentication
7. Redirect to login if not authenticated
8. Basic layout: header with navigation, main content area, footer
9. Responsive design (works on desktop and tablet)
10. Unit tests for authentication flow
11. Manual test: login, logout, access protected pages

#### Story 4.2: Dashboard/Home Screen

As an **admin user**,  
I want **a dashboard showing system overview and recent activity**,  
so that **I can quickly see system health and recent changes**.

**Acceptance Criteria:**

1. Dashboard displays:
   - Total active route subscriptions
   - Total active sources
   - Changes detected in last 7 days
   - Recent changes list (last 5-10, with route, source, timestamp)
   - System health: last successful fetch timestamp per source
2. Quick stats cards/sections
3. Recent changes are clickable (link to change detail page)
4. Sources with recent errors highlighted
5. Sources not checked recently (beyond expected frequency) highlighted
6. Page loads quickly (< 2 seconds)
7. Data fetched via API calls (not direct database access from UI)
8. Manual test: verify all data displays correctly

#### Story 4.3: Route Subscription Management UI

As an **admin user**,  
I want **a UI for managing route subscriptions**,  
so that **I can create, view, edit, and delete route subscriptions without using the API**.

**Acceptance Criteria:**

1. Route list page: displays all route subscriptions in a table
   - Columns: origin, destination, visa_type, email, created_at
   - Sortable by any column
   - Search/filter functionality
2. Create route form:
   - Fields: origin (dropdown/autocomplete), destination (dropdown/autocomplete), visa_type (dropdown), email (text input)
   - Validation: required fields, valid email format, valid country codes
   - Submit creates route via API
   - Success message and redirect to route list
3. Edit route page: pre-filled form, update via API
4. Delete route: confirmation dialog, delete via API
5. View route detail: shows route info and associated sources
6. Error handling: display API errors to user
7. Manual test: create, edit, delete routes via UI

#### Story 4.4: Source Configuration UI

As an **admin user**,  
I want **a UI for managing policy sources**,  
so that **I can configure and monitor sources without using the API**.

**Acceptance Criteria:**

1. Source list page: displays all sources in a table
   - Columns: country, visa_type, URL, fetch_type, check_frequency, last_checked, status
   - Sortable and filterable
   - Status indicators: active, error, never checked
2. Create source form:
   - Fields: country, visa_type, URL, fetch_type (dropdown: HTML, PDF), check_frequency
   - Validation: required fields, valid URL, valid fetch_type
   - Submit creates source via API
3. Edit source page: pre-filled form, update via API
4. Delete source: confirmation dialog (warn if source has versions/changes), delete via API
5. View source detail: shows source info, last check status, recent changes
6. Source status display: last checked timestamp, last change detected, error count
7. Manual test: create, edit, delete sources via UI

#### Story 4.5: Change History View

As an **admin user**,  
I want **a page showing all detected policy changes**,  
so that **I can review the history of changes and verify the system is working**.

**Acceptance Criteria:**

1. Change history page: displays all PolicyChange records in a table
   - Columns: detected_at, route (origin → destination, visa_type), source name, change summary
   - Sortable by date (newest first by default)
   - Filterable by: route, source, date range
   - Pagination for large result sets
2. Each change is clickable (link to change detail page)
3. Change summary: shows first line of diff or "Content changed" if diff is large
4. Visual indicators: new changes highlighted
5. Date range filter: last 7 days, last 30 days, custom range
6. Export functionality (optional): export filtered results to CSV
7. Page loads efficiently even with many changes
8. Manual test: view change history, test filters

#### Story 4.6: Change Detail/Diff View

As an **admin user**,  
I want **a page showing the full diff for a specific policy change**,  
so that **I can see exactly what changed in the policy**.

**Acceptance Criteria:**

1. Change detail page displays:
   - Route information (origin → destination, visa_type)
   - Source name and URL (link to original source)
   - Detected timestamp
   - Full text diff (formatted for readability)
2. Diff display options:
   - Unified diff format (side-by-side or inline)
   - Syntax highlighting if possible (but not required)
   - Line numbers
3. Previous version and new version displayed (if space allows)
4. Link to download diff as text file (optional)
5. Navigation: back to change history, next/previous change
6. Page loads diff efficiently (even for large documents)
7. Manual test: view diff, verify formatting is readable

#### Story 4.7: Manual Trigger/Testing Interface

As an **admin user**,  
I want **a way to manually trigger source fetches**,  
so that **I can test fetchers and verify the system is working**.

**Acceptance Criteria:**

1. Manual trigger page: list of all sources with "Fetch Now" button for each
2. Trigger action:
   - Calls API endpoint to trigger fetch for specific source
   - Shows loading indicator
   - Displays results: success/failure, change detected yes/no, error messages
3. Results display:
   - Fetch status (success/failure)
   - Change detected (yes/no)
   - If changed: link to PolicyChange record
   - Error messages if fetch failed
4. Can trigger multiple sources (one at a time or batch)
5. Trigger logs visible (last trigger timestamp, result)
6. Useful for: testing new sources, debugging fetch issues, demo purposes
7. Manual test: trigger fetch, verify results displayed

#### Story 4.8: System Status/Monitoring View

As an **admin user**,  
I want **a page showing system health and source monitoring status**,  
so that **I can verify all sources are being checked regularly**.

**Acceptance Criteria:**

1. System status page displays:
   - List of all sources with:
     - Last checked timestamp
     - Status (healthy, error, never checked)
     - Last change detected timestamp
     - Error count (if any)
     - Next expected check time
2. Visual indicators: green (healthy), yellow (warning - not checked recently), red (error)
3. Sources sorted by status (errors first)
4. Can trigger manual fetch from this page
5. System-wide stats: total sources, healthy sources, sources with errors
6. Last successful daily job run timestamp
7. Page auto-refreshes or can be manually refreshed
8. Manual test: verify all sources show correct status

---
