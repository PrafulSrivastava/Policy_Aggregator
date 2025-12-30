# API Reference

Complete API reference for the Policy Aggregator FastAPI backend. This document provides all endpoints, request/response models, authentication requirements, and examples needed for frontend development.

## Base URL

- **Development:** `http://localhost:8000`
- **Production:** `https://api.policyaggregator.com`

## Authentication

All endpoints except `/health` and `/auth/login` require authentication using a JWT Bearer token.

### Getting a Token

**POST** `/auth/login`

Request:
```json
{
  "username": "admin",
  "password": "yourpassword"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

**Token Expiration:** Tokens expire after 24 hours. Re-authenticate to get a new token.

---

## Health Check

### GET /health

Check application and database health status.

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Application is healthy

---

## Authentication Endpoints

### POST /auth/login

Authenticate user and receive JWT token.

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "string (required, 1-100 chars)",
  "password": "string (required)"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

**Status Codes:**
- `200 OK` - Login successful
- `401 Unauthorized` - Invalid credentials or inactive account

**Notes:**
- Sets an `access_token` cookie (HttpOnly, Secure) for web requests
- Updates user's `last_login_at` timestamp

### POST /auth/logout

Logout endpoint (clears session cookie).

**Authentication:** Not required

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

**Status Codes:**
- `200 OK` - Logout successful

**Notes:**
- Clears the `access_token` cookie if present
- For JWT tokens, logout is primarily handled client-side by removing the token

### GET /auth/google

Start Google OAuth flow.

**Authentication:** Not required

**Response:** Redirects to Google OAuth authorization URL

**Status Codes:**
- `302 Found` - Redirect to Google
- `501 Not Implemented` - Google OAuth not configured

**Notes:**
- Sets an `oauth_state` cookie for CSRF protection
- Redirects user to Google for authentication

### GET /auth/google/callback

Handle Google OAuth callback.

**Authentication:** Not required

**Query Parameters:**
- `code` (string, optional) - Authorization code from Google
- `state` (string, optional) - State token from Google
- `error` (string, optional) - Error parameter if user denied access

**Response:** Redirects to dashboard on success, login page on error

**Status Codes:**
- `302 Found` - Redirect to dashboard or login page

**Notes:**
- Exchanges authorization code for user info
- Creates/authenticates user
- Sets JWT token in cookie and redirects to dashboard

---

## Dashboard Endpoints

### GET /api/dashboard

Get dashboard statistics including route counts, source counts, recent changes, and source health.

**Authentication:** Required

**Response:**
```json
{
  "totalRoutes": 5,
  "totalSources": 10,
  "activeSources": 8,
  "changesLast7Days": 3,
  "changesLast30Days": 12,
  "recentChanges": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "sourceId": "123e4567-e89b-12d3-a456-426614174001",
      "sourceName": "Germany Student Visa",
      "route": "DE: Student",
      "detectedAt": "2025-01-27T10:00:00Z",
      "hasDiff": true,
      "diffLength": 150
    }
  ],
  "sourceHealth": [
    {
      "sourceId": "123e4567-e89b-12d3-a456-426614174001",
      "sourceName": "Germany Student Visa Source",
      "country": "DE",
      "visaType": "Student",
      "lastCheckedAt": "2025-01-27T10:00:00Z",
      "status": "healthy",
      "consecutiveFailures": 0,
      "lastError": null
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Dashboard statistics retrieved
- `401 Unauthorized` - Missing or invalid authentication token

---

## Route Subscription Endpoints

### GET /api/routes

List route subscriptions with pagination and optional filtering.

**Authentication:** Required

**Query Parameters:**
- `page` (integer, default: 1, min: 1) - Page number (1-indexed)
- `page_size` (integer, default: 20, min: 1, max: 100) - Number of items per page
- `origin_country` (string, optional) - Filter by origin country code (2 characters)
- `destination_country` (string, optional) - Filter by destination country code (2 characters)
- `visa_type` (string, optional) - Filter by visa type
- `is_active` (boolean, optional) - Filter by active status

**Response:**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "origin_country": "IN",
      "destination_country": "DE",
      "visa_type": "Student",
      "email": "user@example.com",
      "is_active": true,
      "created_at": "2025-01-27T10:00:00Z",
      "updated_at": "2025-01-27T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Status Codes:**
- `200 OK` - Successfully retrieved route subscriptions
- `401 Unauthorized` - Missing or invalid authentication token

### POST /api/routes

Create a new route subscription.

**Authentication:** Required

**Request Body:**
```json
{
  "origin_country": "IN",
  "destination_country": "DE",
  "visa_type": "Student",
  "email": "user@example.com",
  "is_active": true
}
```

**Field Validation:**
- `origin_country`: Required, exactly 2 uppercase characters
- `destination_country`: Required, exactly 2 uppercase characters
- `visa_type`: Required, max 50 characters
- `email`: Required, valid email format
- `is_active`: Optional, boolean (default: true)

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "origin_country": "IN",
  "destination_country": "DE",
  "visa_type": "Student",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T10:00:00Z"
}
```

**Status Codes:**
- `201 Created` - Route subscription created successfully
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid authentication token
- `409 Conflict` - Duplicate route subscription exists

**Error Response (409):**
```json
{
  "detail": {
    "code": "DUPLICATE_ROUTE",
    "message": "A route subscription with these parameters already exists",
    "details": {
      "origin_country": "IN",
      "destination_country": "DE",
      "visa_type": "Student",
      "email": "user@example.com"
    }
  }
}
```

### GET /api/routes/{route_id}

Get a specific route subscription by ID.

**Authentication:** Required

**Path Parameters:**
- `route_id` (UUID, required) - Route subscription UUID

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "origin_country": "IN",
  "destination_country": "DE",
  "visa_type": "Student",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Route subscription found
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Route subscription not found

**Error Response (404):**
```json
{
  "detail": {
    "code": "ROUTE_NOT_FOUND",
    "message": "Route subscription with id {route_id} not found"
  }
}
```

### PUT /api/routes/{route_id}

Update a route subscription. Supports partial updates.

**Authentication:** Required

**Path Parameters:**
- `route_id` (UUID, required) - Route subscription UUID

**Request Body:**
```json
{
  "origin_country": "IN",
  "destination_country": "US",
  "visa_type": "Work",
  "email": "newemail@example.com",
  "is_active": false
}
```

**Field Validation:**
- All fields are optional (partial updates supported)
- `origin_country`: If provided, exactly 2 uppercase characters
- `destination_country`: If provided, exactly 2 uppercase characters
- `visa_type`: If provided, max 50 characters
- `email`: If provided, valid email format
- `is_active`: If provided, boolean

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "origin_country": "IN",
  "destination_country": "US",
  "visa_type": "Work",
  "email": "newemail@example.com",
  "is_active": false,
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T11:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Route subscription updated successfully
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Route subscription not found

### DELETE /api/routes/{route_id}

Delete a route subscription by ID.

**Authentication:** Required

**Path Parameters:**
- `route_id` (UUID, required) - Route subscription UUID

**Response:** No content

**Status Codes:**
- `204 No Content` - Route subscription deleted successfully
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Route subscription not found

---

## Source Endpoints

### GET /api/sources

List sources with pagination and optional filtering.

**Authentication:** Required

**Query Parameters:**
- `page` (integer, default: 1, min: 1) - Page number (1-indexed)
- `page_size` (integer, default: 20, min: 1, max: 100) - Number of items per page
- `country` (string, optional) - Filter by country code (2 characters)
- `visa_type` (string, optional) - Filter by visa type
- `is_active` (boolean, optional) - Filter by active status

**Response:**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "country": "DE",
      "visa_type": "Student",
      "url": "https://example.com/policy",
      "name": "Germany Student Visa Source",
      "fetch_type": "html",
      "check_frequency": "daily",
      "is_active": true,
      "metadata": {},
      "last_checked_at": null,
      "last_change_detected_at": null,
      "created_at": "2025-01-27T10:00:00Z",
      "updated_at": "2025-01-27T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Status Codes:**
- `200 OK` - Successfully retrieved sources
- `401 Unauthorized` - Missing or invalid authentication token

### POST /api/sources

Create a new source.

**Authentication:** Required

**Request Body:**
```json
{
  "country": "DE",
  "visa_type": "Student",
  "url": "https://example.com/policy",
  "name": "Germany Student Visa Source",
  "fetch_type": "html",
  "check_frequency": "daily",
  "is_active": true,
  "metadata": {}
}
```

**Field Validation:**
- `country`: Required, exactly 2 uppercase characters
- `visa_type`: Required, max 50 characters
- `url`: Required, must start with http:// or https://
- `name`: Required, max 255 characters
- `fetch_type`: Required, enum: `"html"` or `"pdf"`
- `check_frequency`: Required, enum: `"daily"`, `"weekly"`, or `"custom"`
- `is_active`: Optional, boolean (default: true)
- `metadata`: Optional, JSON object (default: {})

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "country": "DE",
  "visa_type": "Student",
  "url": "https://example.com/policy",
  "name": "Germany Student Visa Source",
  "fetch_type": "html",
  "check_frequency": "daily",
  "is_active": true,
  "metadata": {},
  "last_checked_at": null,
  "last_change_detected_at": null,
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T10:00:00Z"
}
```

**Status Codes:**
- `201 Created` - Source created successfully
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid authentication token
- `409 Conflict` - Duplicate source exists

**Error Response (409):**
```json
{
  "detail": {
    "code": "DUPLICATE_SOURCE",
    "message": "A source with these parameters already exists",
    "details": {
      "url": "https://example.com/policy",
      "country": "DE",
      "visa_type": "Student"
    }
  }
}
```

### GET /api/sources/{source_id}

Get a specific source by ID with metadata.

**Authentication:** Required

**Path Parameters:**
- `source_id` (UUID, required) - Source UUID

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "country": "DE",
  "visa_type": "Student",
  "url": "https://example.com/policy",
  "name": "Germany Student Visa Source",
  "fetch_type": "html",
  "check_frequency": "daily",
  "is_active": true,
  "metadata": {},
  "last_checked_at": null,
  "last_change_detected_at": null,
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Source found
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Source not found

**Error Response (404):**
```json
{
  "detail": {
    "code": "SOURCE_NOT_FOUND",
    "message": "Source with id {source_id} not found"
  }
}
```

### PUT /api/sources/{source_id}

Update a source configuration. Supports partial updates.

**Authentication:** Required

**Path Parameters:**
- `source_id` (UUID, required) - Source UUID

**Request Body:**
```json
{
  "url": "https://updated.com/policy",
  "name": "Updated Source Name",
  "check_frequency": "weekly",
  "is_active": false
}
```

**Field Validation:**
- All fields are optional (partial updates supported)
- `country`: If provided, exactly 2 uppercase characters
- `visa_type`: If provided, max 50 characters
- `url`: If provided, must start with http:// or https://
- `name`: If provided, max 255 characters
- `fetch_type`: If provided, enum: `"html"` or `"pdf"`
- `check_frequency`: If provided, enum: `"daily"`, `"weekly"`, or `"custom"`
- `is_active`: If provided, boolean
- `metadata`: If provided, JSON object

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "country": "DE",
  "visa_type": "Student",
  "url": "https://updated.com/policy",
  "name": "Updated Source Name",
  "fetch_type": "html",
  "check_frequency": "weekly",
  "is_active": false,
  "metadata": {},
  "last_checked_at": null,
  "last_change_detected_at": null,
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T11:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Source updated successfully
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Source not found

### DELETE /api/sources/{source_id}

Delete a source by ID. Cascade delete will remove related PolicyVersions and PolicyChanges.

**Authentication:** Required

**Path Parameters:**
- `source_id` (UUID, required) - Source UUID

**Response:** No content

**Status Codes:**
- `204 No Content` - Source deleted successfully
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Source not found

**Notes:**
- Cascade delete is handled by the database
- Related PolicyVersions and PolicyChanges are automatically deleted

### POST /api/sources/{source_id}/trigger

Manually trigger the fetch and process pipeline for a specific source.

**Authentication:** Required

**Path Parameters:**
- `source_id` (UUID, required) - Source UUID to fetch and process

**Response:**
```json
{
  "success": true,
  "sourceId": "123e4567-e89b-12d3-a456-426614174000",
  "changeDetected": false,
  "policyVersionId": "123e4567-e89b-12d3-a456-426614174001",
  "policyChangeId": null,
  "error": null,
  "fetchedAt": "2025-01-27T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Pipeline execution result
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Source not found

**Notes:**
- Executes the complete pipeline: fetch → normalize → detect changes → store version → create change if detected
- This is an asynchronous operation that may take time depending on the source

---

## Job Endpoints

### POST /api/jobs/daily-fetch

Manually trigger the daily fetch job that processes all active sources with daily check frequency.

**Authentication:** Required

**Response:**
```json
{
  "startedAt": "2025-01-27T10:00:00Z",
  "completedAt": "2025-01-27T10:05:00Z",
  "sourcesProcessed": 5,
  "sourcesSucceeded": 4,
  "sourcesFailed": 1,
  "changesDetected": 2,
  "alertsSent": 3,
  "errors": []
}
```

**Status Codes:**
- `200 OK` - Job execution result
- `401 Unauthorized` - Missing or invalid authentication token

**Notes:**
- Processes all active sources with `check_frequency: "daily"`
- Triggers alert engine when changes are detected
- Handles errors gracefully (one source failure doesn't stop others)
- This is a long-running operation

---

## Status Endpoints

### GET /api/status

Get comprehensive system status including all sources with health information, statistics, and monitoring data.

**Authentication:** Required

**Response:**
```json
{
  "sources": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Germany Student Visa Source",
      "country": "DE",
      "visa_type": "Student",
      "url": "https://example.com/policy",
      "fetch_type": "html",
      "check_frequency": "daily",
      "is_active": true,
      "last_checked_at": "2025-01-27T10:00:00Z",
      "last_change_detected_at": "2025-01-26T10:00:00Z",
      "status": "active",
      "consecutive_fetch_failures": 0,
      "last_fetch_error": null,
      "next_check_time": "2025-01-28T10:00:00Z"
    }
  ],
  "statistics": {
    "total_sources": 10,
    "healthy_sources": 8,
    "error_sources": 1,
    "stale_sources": 1,
    "never_checked_sources": 0
  },
  "last_daily_job_run": null
}
```

**Status Codes:**
- `200 OK` - System status data
- `401 Unauthorized` - Missing or invalid authentication token

---

## Policy Changes Endpoints

### GET /api/changes

List policy changes with pagination and optional filtering.

**Authentication:** Required

**Query Parameters:**
- `page` (integer, default: 1, min: 1) - Page number (1-indexed)
- `page_size` (integer, default: 50, min: 1, max: 100) - Number of items per page
- `route_id` (string, optional) - Filter by route subscription UUID
- `source_id` (string, optional) - Filter by source UUID
- `start_date` (string, optional) - Filter by start date (ISO format, e.g., "2025-01-01T00:00:00Z")
- `end_date` (string, optional) - Filter by end date (ISO format, e.g., "2025-01-31T23:59:59Z")
- `sort_by` (string, default: "detected_at") - Column to sort by
- `sort_order` (string, default: "desc") - Sort order: `"asc"` or `"desc"`

**Response:**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "detected_at": "2025-01-27T10:00:00Z",
      "source": {
        "id": "456e7890-e89b-12d3-a456-426614174000",
        "name": "Germany Student Visa Source",
        "country": "DE",
        "visa_type": "Student"
      },
      "route": {
        "id": "789e0123-e89b-12d3-a456-426614174000",
        "origin_country": "IN",
        "destination_country": "DE",
        "visa_type": "Student",
        "display": "IN → DE, Student"
      },
      "summary": "Content changed",
      "is_new": true,
      "diff_length": 150
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50,
  "pages": 1
}
```

**Status Codes:**
- `200 OK` - Successfully retrieved changes
- `401 Unauthorized` - Missing or invalid authentication token

### GET /api/changes/{change_id}

Get detailed information for a specific policy change including diff, versions, and navigation.

**Authentication:** Required

**Path Parameters:**
- `change_id` (UUID, required) - PolicyChange UUID

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "detected_at": "2025-01-27T10:00:00Z",
  "diff": "--- old\n+++ new\n...",
  "diff_length": 150,
  "source": {
    "id": "456e7890-e89b-12d3-a456-426614174000",
    "name": "Germany Student Visa Source",
    "url": "https://example.com/policy",
    "country": "DE",
    "visa_type": "Student"
  },
  "route": {
    "id": "789e0123-e89b-12d3-a456-426614174000",
    "origin_country": "IN",
    "destination_country": "DE",
    "visa_type": "Student",
    "display": "IN → DE, Student"
  },
  "old_version": {
    "id": "abc123...",
    "content_hash": "...",
    "raw_text": "...",
    "fetched_at": "2025-01-26T10:00:00Z",
    "content_length": 1000
  },
  "new_version": {
    "id": "def456...",
    "content_hash": "...",
    "raw_text": "...",
    "fetched_at": "2025-01-27T10:00:00Z",
    "content_length": 1200
  },
  "previous_change_id": "111e2222-e89b-12d3-a456-426614174000",
  "next_change_id": "333e4444-e89b-12d3-a456-426614174000"
}
```

**Status Codes:**
- `200 OK` - Change detail found
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Change not found

**Error Response (404):**
```json
{
  "detail": {
    "code": "CHANGE_NOT_FOUND",
    "message": "Policy change with id {change_id} not found"
  }
}
```

### GET /api/changes/{change_id}/download

Download the diff text for a specific policy change as a plain text file.

**Authentication:** Required

**Path Parameters:**
- `change_id` (UUID, required) - PolicyChange UUID

**Response:** Plain text file with diff content

**Content-Type:** `text/plain`

**Headers:**
```
Content-Disposition: attachment; filename=diff_{source_name}_{timestamp}.txt
```

**Status Codes:**
- `200 OK` - Diff text file
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Change not found

### GET /api/changes/export

Export filtered policy changes to CSV format.

**Authentication:** Required

**Query Parameters:**
- `route_id` (string, optional) - Filter by route subscription UUID
- `source_id` (string, optional) - Filter by source UUID
- `start_date` (string, optional) - Filter by start date (ISO format)
- `end_date` (string, optional) - Filter by end date (ISO format)

**Response:** CSV file with changes

**Content-Type:** `text/csv`

**Headers:**
```
Content-Disposition: attachment; filename=policy_changes_{timestamp}.csv
```

**CSV Columns:**
- Detected At
- Source Name
- Source Country
- Source Visa Type
- Route
- Change Summary
- Diff Length

**Status Codes:**
- `200 OK` - CSV file with changes
- `401 Unauthorized` - Missing or invalid authentication token

---

## Error Handling

### Error Response Format

All error responses follow a consistent format:

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error details (optional)
    }
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `DUPLICATE_ROUTE` | 409 | Duplicate route subscription exists |
| `DUPLICATE_SOURCE` | 409 | Duplicate source exists |
| `INTERNAL_ERROR` | 500 | Server error |

### Validation Errors

When validation fails, FastAPI returns detailed validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Pagination

List endpoints support pagination via `page` and `page_size` query parameters.

**Response Format:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

**Pagination Parameters:**
- `page`: Page number (1-indexed, default: 1, min: 1)
- `page_size`: Items per page (default varies by endpoint, max: 100)

---

## Data Types

### UUID
All IDs are UUIDs (Universally Unique Identifiers) in the format: `123e4567-e89b-12d3-a456-426614174000`

### DateTime
All timestamps are in ISO 8601 format with UTC timezone: `2025-01-27T10:00:00Z`

### Country Codes
Country codes are 2-character uppercase ISO codes (e.g., `"IN"`, `"DE"`, `"US"`)

### Enums

**FetchType:**
- `"html"` - HTML content fetching
- `"pdf"` - PDF content fetching

**CheckFrequency:**
- `"daily"` - Check once per day
- `"weekly"` - Check once per week
- `"custom"` - Custom check frequency

---

## Rate Limiting

Currently, there are no rate limits implemented. This may change in future versions.

---

## CORS

CORS is configured to allow requests from specified origins. Check the backend configuration for allowed origins.

---

## OpenAPI Documentation

FastAPI automatically generates OpenAPI 3.0 documentation. Access it at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

The OpenAPI schema provides interactive API documentation with request/response examples and the ability to test endpoints directly.

---

## Examples

### Example: Create a Route Subscription

```bash
curl -X POST "http://localhost:8000/api/routes" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "origin_country": "IN",
    "destination_country": "DE",
    "visa_type": "Student",
    "email": "user@example.com",
    "is_active": true
  }'
```

### Example: List Sources with Filtering

```bash
curl -X GET "http://localhost:8000/api/sources?country=DE&visa_type=Student&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example: Trigger Source Fetch

```bash
curl -X POST "http://localhost:8000/api/sources/123e4567-e89b-12d3-a456-426614174000/trigger" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example: Get Policy Changes with Date Range

```bash
curl -X GET "http://localhost:8000/api/changes?start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z&page=1&page_size=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Notes for Frontend Development

1. **Authentication:** Store the JWT token securely (e.g., in localStorage or httpOnly cookie) and include it in all API requests.

2. **Error Handling:** Always check the response status code and handle errors appropriately. Display user-friendly error messages.

3. **Pagination:** Implement pagination controls for list endpoints. The response includes `total`, `page`, and `page_size` for building pagination UI.

4. **Loading States:** Some operations (like triggering source fetches) may take time. Show loading indicators and handle async operations properly.

5. **Date Formatting:** All dates are in ISO 8601 format with UTC timezone. Format them appropriately for your locale in the frontend.

6. **UUID Handling:** All IDs are UUIDs. Ensure your frontend can handle UUID format correctly.

7. **Validation:** Client-side validation should match the API validation rules. However, always validate on the server side as well.

8. **CORS:** If developing locally, ensure your frontend origin is included in the backend CORS configuration.

---

## Version

This API reference is for **API Version 1.0.0**.

For the latest updates and changes, check the OpenAPI documentation at `/docs` endpoint.

