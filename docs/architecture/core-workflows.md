# Core Workflows

This section illustrates key system workflows using sequence diagrams, showing component interactions including external APIs, error handling paths, and async operations.

### Workflow 1: Daily Fetch Pipeline (Automated)

**Description:** The primary automated workflow that runs daily via GitHub Actions cron. Fetches all active sources, normalizes content, detects changes, and sends email alerts when changes are detected.

```mermaid
sequenceDiagram
    participant GH as GitHub Actions Cron
    participant FM as Fetcher Manager
    participant SF as Source Fetcher
    participant GS as Government Source
    participant CN as Content Normalizer
    participant CD as Change Detector
    participant DG as Diff Generator
    participant AE as Alert Engine
    participant Repo as Repository
    participant DB as PostgreSQL
    participant Resend as Resend API

    GH->>FM: Trigger daily fetch pipeline
    FM->>Repo: Get all active sources
    Repo->>DB: SELECT * FROM sources WHERE is_active = true
    DB-->>Repo: List of sources
    Repo-->>FM: Active sources

    loop For each source
        FM->>SF: fetch(source)
        SF->>GS: HTTP GET request
        GS-->>SF: HTML/PDF content
        
        alt Fetch successful
            SF-->>FM: FetchResult(raw_text, metadata)
            FM->>CN: normalize(raw_text, source_metadata)
            CN-->>FM: normalized_text
            FM->>CD: detect_change(source_id, normalized_text)
            CD->>Repo: get_latest_version(source_id)
            Repo->>DB: SELECT * FROM policy_versions WHERE source_id = ? ORDER BY fetched_at DESC LIMIT 1
            DB-->>Repo: Previous version (or null)
            Repo-->>CD: Previous version
            
            alt Change detected (hash differs)
                CD->>Repo: create_policy_version(new_version)
                Repo->>DB: INSERT INTO policy_versions
                CD->>DG: generate_diff(old_content, new_content)
                DG-->>CD: diff_text
                CD->>Repo: create_policy_change(change_record)
                Repo->>DB: INSERT INTO policy_changes
                CD->>AE: send_change_alert(policy_change_id)
                AE->>Repo: find_matching_routes(policy_change)
                Repo->>DB: SELECT * FROM route_subscriptions WHERE origin_country = ? AND destination_country = ? AND visa_type = ?
                DB-->>Repo: Matching routes
                Repo-->>AE: Route subscriptions
                
                loop For each matching route
                    AE->>AE: format_email_content(change, route)
                    AE->>Resend: POST /emails (send alert)
                    Resend-->>AE: Email sent (email_id)
                    AE->>Repo: create_email_alert(alert_record)
                    Repo->>DB: INSERT INTO email_alerts
                end
            else No change (hash matches)
                CD->>Repo: create_policy_version(new_version)
                Repo->>DB: INSERT INTO policy_versions
                Note over CD: Version stored but no change detected
            end
        else Fetch failed
            SF-->>FM: FetchError(error_message)
            FM->>Repo: log_fetch_error(source_id, error)
            Repo->>DB: UPDATE sources SET last_error = ?
            Note over FM: Continue with next source (error isolation)
        end
    end
    
    FM-->>GH: Pipeline completed (summary)
```

**Key Points:**
- Error isolation: One source failure doesn't stop the pipeline
- Immutable versions: New PolicyVersion created even if no change detected
- Change detection: Hash comparison determines if change occurred
- Alert matching: Routes matched by country and visa type
- Async operations: All database operations are synchronous (can be made async later)

### Workflow 2: Manual Source Fetch (Testing/Debugging)

**Description:** Admin-initiated workflow for manually triggering a source fetch via the admin interface. Used for testing source configurations and debugging fetch issues.

```mermaid
sequenceDiagram
    participant Admin as Admin User
    participant UI as Admin UI
    participant API as REST API
    participant Auth as Authentication
    participant FM as Fetcher Manager
    participant SF as Source Fetcher
    participant GS as Government Source
    participant CN as Content Normalizer
    participant CD as Change Detector
    participant Repo as Repository
    participant DB as PostgreSQL

    Admin->>UI: Click "Trigger Fetch" for source
    UI->>API: POST /api/sources/{id}/trigger
    API->>Auth: Validate JWT token
    Auth-->>API: Token valid
    API->>Repo: get_source(source_id)
    Repo->>DB: SELECT * FROM sources WHERE id = ?
    DB-->>Repo: Source record
    Repo-->>API: Source
    
    API->>FM: fetch_source(source_id)
    FM->>SF: fetch(source)
    SF->>GS: HTTP GET request
    GS-->>SF: HTML/PDF content
    SF-->>FM: FetchResult
    
    FM->>CN: normalize(raw_text)
    CN-->>FM: normalized_text
    FM->>CD: detect_change(source_id, normalized_text)
    CD->>Repo: get_latest_version(source_id)
    Repo->>DB: SELECT * FROM policy_versions WHERE source_id = ? ORDER BY fetched_at DESC LIMIT 1
    DB-->>Repo: Previous version
    Repo-->>CD: Previous version
    
    alt Change detected
        CD->>Repo: create_policy_version(new_version)
        CD->>Repo: create_policy_change(change_record)
        CD-->>FM: ChangeResult(change_detected=true, policy_change_id)
    else No change
        CD->>Repo: create_policy_version(new_version)
        CD-->>FM: ChangeResult(change_detected=false)
    end
    
    FM-->>API: FetchResult with change status
    API-->>UI: JSON response (success, hash, change_detected, etc.)
    UI-->>Admin: Display fetch results
```

**Key Points:**
- Authentication required for manual trigger
- Same pipeline as automated fetch (code reuse)
- Results returned immediately to admin
- Useful for testing source configurations before enabling automated checks

### Workflow 3: Policy Change Detection and Alert Flow

**Description:** Detailed flow showing what happens when a policy change is detected, from hash comparison through email alert delivery.

```mermaid
sequenceDiagram
    participant CD as Change Detector
    participant Repo as Repository
    participant DB as PostgreSQL
    participant DG as Diff Generator
    participant AE as Alert Engine
    participant Resend as Resend API
    participant User as Route Subscriber

    CD->>CD: Calculate SHA256 hash of normalized content
    CD->>Repo: get_latest_version(source_id)
    Repo->>DB: SELECT content_hash FROM policy_versions WHERE source_id = ? ORDER BY fetched_at DESC LIMIT 1
    DB-->>Repo: Previous hash
    Repo-->>CD: Previous hash (or null if first fetch)
    
    alt Hash differs (change detected)
        CD->>Repo: create_policy_version(new_version)
        Repo->>DB: INSERT INTO policy_versions (source_id, content_hash, raw_text, fetched_at)
        DB-->>Repo: New version created
        
        CD->>Repo: get_policy_version_by_hash(old_hash)
        Repo->>DB: SELECT * FROM policy_versions WHERE content_hash = ?
        DB-->>Repo: Old version
        Repo-->>CD: Old version content
        
        CD->>DG: generate_diff(old_content, new_content)
        DG->>DG: Use difflib.unified_diff()
        DG-->>CD: diff_text (unified diff format)
        
        CD->>Repo: create_policy_change(source_id, old_hash, new_hash, diff, detected_at)
        Repo->>DB: INSERT INTO policy_changes
        DB-->>Repo: PolicyChange created
        Repo-->>CD: policy_change_id
        
        CD->>AE: send_change_alert(policy_change_id)
        AE->>Repo: get_policy_change(policy_change_id)
        Repo->>DB: SELECT * FROM policy_changes WHERE id = ?
        DB-->>Repo: PolicyChange with source info
        Repo-->>AE: PolicyChange
        
        AE->>Repo: get_source(policy_change.source_id)
        Repo->>DB: SELECT * FROM sources WHERE id = ?
        DB-->>Repo: Source (country, visa_type)
        Repo-->>AE: Source
        
        AE->>Repo: find_matching_routes(source.country, source.visa_type)
        Repo->>DB: SELECT * FROM route_subscriptions WHERE destination_country = ? AND visa_type = ? AND is_active = true
        DB-->>Repo: Matching route subscriptions
        Repo-->>AE: Route subscriptions
        
        loop For each matching route subscription
            AE->>AE: format_email_content(policy_change, route, source)
            AE->>Resend: POST /emails
            Note over Resend: Email: route, source, timestamp, diff preview, link
            Resend-->>AE: Email sent (email_id)
            AE->>Repo: create_email_alert(policy_change_id, route_id, email_id, sent_at)
            Repo->>DB: INSERT INTO email_alerts
            Resend->>User: Deliver email to route subscriber
        end
        
        AE-->>CD: Alerts sent
    else Hash matches (no change)
        CD->>Repo: create_policy_version(new_version)
        Repo->>DB: INSERT INTO policy_versions
        Note over CD: Version stored for history, no change detected
        CD-->>CD: No further action
    end
```

**Key Points:**
- Hash comparison is the primary change detection mechanism
- Diff generation only occurs when change is detected (efficiency)
- Route matching uses country and visa type (not stored foreign keys)
- Email alerts sent to all matching route subscriptions
- Each alert delivery is tracked in EmailAlert table

### Workflow 4: Admin Login and Session Management

**Description:** User authentication flow for admin access to the interface and API.

```mermaid
sequenceDiagram
    participant Admin as Admin User
    participant UI as Admin UI
    participant API as REST API
    participant Auth as Authentication Service
    participant Repo as Repository
    participant DB as PostgreSQL

    Admin->>UI: Enter username/password
    UI->>API: POST /auth/login {username, password}
    API->>Auth: login(username, password)
    Auth->>Repo: get_user_by_username(username)
    Repo->>DB: SELECT * FROM users WHERE username = ?
    DB-->>Repo: User record (with hashed_password)
    Repo-->>Auth: User
    
    Auth->>Auth: verify_password(password, user.hashed_password)
    
    alt Credentials valid
        Auth->>Auth: generate_jwt_token(user_id)
        Auth-->>API: JWT token
        API-->>UI: {access_token, token_type: "bearer"}
        UI->>UI: Store token in localStorage/sessionStorage
        UI-->>Admin: Redirect to dashboard
        
        Note over Admin,UI: Subsequent requests include: Authorization: Bearer <token>
        
        Admin->>UI: Navigate to protected page
        UI->>API: GET /api/routes (with Authorization header)
        API->>Auth: validate_token(token)
        Auth->>Auth: Decode and verify JWT
        Auth-->>API: Token valid, user_id
        API->>Repo: get_routes()
        Repo->>DB: SELECT * FROM route_subscriptions
        DB-->>Repo: Routes
        Repo-->>API: Routes
        API-->>UI: JSON response
        UI-->>Admin: Display routes
    else Credentials invalid
        Auth-->>API: Authentication failed
        API-->>UI: 401 Unauthorized {error: "Invalid credentials"}
        UI-->>Admin: Display error message
    end
```

**Key Points:**
- JWT tokens for stateless authentication
- Password hashing with bcrypt
- Token stored client-side (localStorage/sessionStorage)
- All protected endpoints validate token
- Token expiration (24 hours) handled by JWT validation

### Workflow 5: View Change History (Admin Interface)

**Description:** Admin viewing policy changes with filtering and detail view.

```mermaid
sequenceDiagram
    participant Admin as Admin User
    participant UI as Admin UI
    participant API as REST API
    participant Auth as Authentication
    participant Repo as Repository
    participant DB as PostgreSQL

    Admin->>UI: Navigate to Change History page
    UI->>UI: Apply filters (route, source, date range)
    UI->>API: GET /api/changes?routeId=...&startDate=...&endDate=...&page=1
    API->>Auth: Validate JWT token
    Auth-->>API: Token valid
    
    API->>Repo: get_policy_changes(filters, pagination)
    Repo->>DB: SELECT * FROM policy_changes WHERE ... ORDER BY detected_at DESC LIMIT 20 OFFSET 0
    DB-->>Repo: Policy changes
    Repo-->>API: Changes list
    
    API-->>UI: JSON response {items: [...], total: 50, page: 1}
    UI-->>Admin: Display changes table
    
    Admin->>UI: Click on change to view details
    UI->>API: GET /api/changes/{id}
    API->>Auth: Validate token
    Auth-->>API: Token valid
    API->>Repo: get_policy_change_with_details(change_id)
    Repo->>DB: SELECT pc.*, s.*, pv_old.*, pv_new.* FROM policy_changes pc JOIN sources s ON pc.source_id = s.id JOIN policy_versions pv_old ON pc.old_version_id = pv_old.id JOIN policy_versions pv_new ON pc.new_version_id = pv_new.id WHERE pc.id = ?
    DB-->>Repo: Change with full details
    Repo-->>API: PolicyChange with source and versions
    API-->>UI: JSON response with full diff
    UI-->>Admin: Display change detail view with diff
```

**Key Points:**
- Filtering and pagination for large change lists
- Detailed view includes full diff and source information
- Efficient database queries with JOINs for related data
- Authentication required for all change history access

### Error Handling Patterns

All workflows include error handling:

1. **Fetch Errors:** Isolated per source, logged, pipeline continues
2. **Database Errors:** Transaction rollback, error logged, user-friendly error message
3. **Email Send Errors:** Retry with exponential backoff, logged, doesn't block change detection
4. **Authentication Errors:** 401 response, clear error message, no token exposure
5. **Validation Errors:** 400 response with field-specific error messages

**Retry Logic:**
- Source fetches: 2-3 retries with exponential backoff (1s, 2s, 4s delays)
- Email sends: 2-3 retries with exponential backoff
- Database operations: No retries (fail fast, log error)

---
