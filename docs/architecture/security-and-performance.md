# Security and Performance

This section defines security and performance considerations for the fullstack application, ensuring the system is secure, performant, and meets non-functional requirements.

### Security Requirements

#### Frontend Security

**CSP Headers (Content Security Policy):**
- **Policy:** `default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; img-src 'self' data:; font-src 'self'; connect-src 'self'`
- **Rationale:** Prevents XSS attacks by restricting resource loading. Allows inline scripts/styles for Jinja2 templates and Tailwind CDN.
- **Implementation:** Set via FastAPI middleware or Railway headers

**XSS Prevention:**
- **Strategy:** Jinja2 auto-escaping enabled for all template variables
- **Implementation:** All user input and database content automatically escaped in templates
- **Additional:** Sanitize any user-provided content before rendering
- **Example:** `{{ user_input|e }}` or automatic escaping in Jinja2

**Secure Storage:**
- **Strategy:** No sensitive data stored client-side
- **JWT Tokens:** Stored in HTTP-only cookies (preferred) or localStorage (fallback)
- **No PII in LocalStorage:** Only non-sensitive UI state
- **Session Management:** Server-side session validation

#### Backend Security

**Input Validation:**
- **Approach:** Pydantic models for all API request/response validation
- **Implementation:** FastAPI automatically validates request bodies against Pydantic schemas
- **Additional Validation:** Custom validators for business rules (email format, country codes, etc.)
- **SQL Injection Prevention:** SQLAlchemy ORM with parameterized queries (no raw SQL with user input)
- **Example:**
```python
from pydantic import BaseModel, EmailStr, validator

class RouteSubscriptionCreate(BaseModel):
    origin_country: str
    destination_country: str
    visa_type: str
    email: EmailStr
    
    @validator('origin_country', 'destination_country')
    def validate_country_code(cls, v):
        if len(v) != 2 or not v.isalpha():
            raise ValueError('Country code must be 2 letters')
        return v.upper()
```

**Rate Limiting:**
- **Configuration:** Not implemented in MVP (low traffic expected)
- **Future (Epic 8):** Implement rate limiting for public API:
  - Per-IP rate limiting: 100 requests/minute
  - Per-API-key rate limiting: Based on subscription tier
  - Use `slowapi` or similar middleware
- **Admin API:** No rate limiting for MVP (single admin user)

**CORS Policy:**
- **Configuration:** CORS not needed for MVP (same-origin requests)
- **Future:** If API accessed from different origins:
  - Allow specific origins only
  - Credentials: true (for cookies)
  - Methods: GET, POST, PUT, DELETE
  - Headers: Authorization, Content-Type

#### Authentication Security

**Token Storage:**
- **Strategy:** JWT tokens in HTTP-only cookies (primary) or Bearer header (API)
- **Cookie Settings:**
  - `HttpOnly`: true (prevents JavaScript access)
  - `Secure`: true (HTTPS only in production)
  - `SameSite`: Strict (CSRF protection)
  - `Max-Age`: 24 hours (86400 seconds)
- **Token Format:** JWT with user ID, expiration, issued-at timestamp

**Session Management:**
- **Approach:** Stateless JWT tokens (no server-side session storage)
- **Token Expiration:** 24 hours (configurable via `JWT_EXPIRE_HOURS`)
- **Token Refresh:** Not implemented in MVP (user re-authenticates)
- **Logout:** Client deletes token, server invalidates (optional token blacklist for MVP)

**Password Policy:**
- **Requirements:**
  - Minimum length: 12 characters (strong password)
  - Complexity: Not enforced in MVP (admin user sets strong password)
  - Hashing: bcrypt with cost factor 12
  - Storage: Hashed password only (never plain text)
- **Future:** Add password complexity requirements if multi-user support added

**Additional Security Measures:**
- **HTTPS:** Enforced in production (Railway automatic)
- **Environment Variables:** All secrets in environment variables, never in code
- **Database Credentials:** Stored in Railway environment variables
- **API Keys:** Resend API key in environment variables
- **Error Messages:** Generic error messages (don't leak system information)
- **Logging:** No sensitive data in logs (passwords, tokens, etc.)

### Performance Optimization

#### Frontend Performance

**Bundle Size Target:**
- **HTML:** < 50KB (gzipped) per page
- **CSS:** < 20KB (gzipped, Tailwind purged)
- **JavaScript:** < 30KB (gzipped)
- **Total Initial Load:** < 100KB (excluding API data)
- **Rationale:** Server-side rendering means minimal JavaScript, Tailwind purging removes unused styles

**Loading Strategy:**
- **Server-Side Rendering:** Fast initial page load (HTML rendered on server)
- **Static Assets:** Served with cache headers (1 year for CSS/JS, versioned)
- **API Calls:** Fetch data on page load, show loading states
- **Lazy Loading:** Not needed for MVP (small admin interface)

**Caching Strategy:**
- **Static Assets:** Long cache (1 year) with versioning/hashing
- **API Responses:** Short cache (5 minutes) for dynamic data
- **HTML Pages:** No cache (always fresh, server-rendered)
- **Browser Cache:** Leverage browser caching for static assets

#### Backend Performance

**Response Time Target:**
- **API Endpoints:** < 200ms for list queries, < 300ms for detail queries
- **Page Rendering:** < 500ms for template rendering
- **Database Queries:** < 100ms for simple queries, < 500ms for complex queries
- **Change Detection:** < 1 second per source (including fetch + normalization + hash)

**Database Optimization:**
- **Indexes:** All foreign keys indexed, composite indexes for common queries
- **Query Optimization:** Use `EXPLAIN ANALYZE` to optimize slow queries
- **Connection Pooling:** SQLAlchemy connection pool (10-20 connections)
- **Query Patterns:**
  - Use `LIMIT` and `OFFSET` for pagination
  - Avoid N+1 queries (use JOINs or eager loading)
  - Index on frequently filtered columns (`is_active`, `detected_at`, etc.)

**Caching Strategy:**
- **MVP:** No caching layer (direct database queries)
- **Future:** Add Redis caching if performance becomes an issue:
  - Cache route subscriptions list (TTL: 5 minutes)
  - Cache source configurations (TTL: 5 minutes)
  - Cache dashboard statistics (TTL: 1 minute)
- **Database Query Cache:** PostgreSQL query cache (automatic)

**Concurrent Processing:**
- **Source Fetching:** Concurrent fetches using `asyncio` (up to 5 concurrent)
- **Change Detection:** Sequential per source (can be parallelized later)
- **Email Sending:** Sequential (can be parallelized if volume increases)

#### Performance Monitoring

**Metrics to Track:**
- **API Response Times:** Track p50, p95, p99 response times
- **Database Query Times:** Monitor slow queries (> 500ms)
- **Source Fetch Times:** Track fetch duration per source
- **Error Rates:** Monitor 4xx and 5xx error rates
- **Page Load Times:** Frontend performance metrics

**Tools:**
- **Development:** Python `cProfile` for profiling
- **Production:** Railway logs and metrics dashboard
- **Future:** Add APM tool (Sentry, DataDog) if needed

**Performance Budget:**
- **Page Load:** < 2 seconds (Time to Interactive)
- **API Response:** < 300ms (p95)
- **Database Query:** < 500ms (p95)
- **Daily Pipeline:** Complete within 30 minutes (for all sources)

### Security Best Practices

**Code Security:**
- **Dependencies:** Regularly update dependencies, scan for vulnerabilities
- **Secrets Management:** Never commit secrets to git, use environment variables
- **Input Sanitization:** Validate and sanitize all user input
- **Error Handling:** Don't expose stack traces in production
- **Logging:** Log security events (failed logins, suspicious activity)

**Infrastructure Security:**
- **HTTPS:** Enforced in production (Railway automatic)
- **Database:** Access restricted to application only (Railway managed)
- **Backups:** Regular database backups (Railway automatic)
- **Updates:** Keep dependencies and infrastructure updated

**Compliance:**
- **GDPR:** Minimal data collection (NFR9), data stored in EU region (Railway EU)
- **Data Retention:** Policy versions retained indefinitely (audit trail)
- **User Rights:** Data export and deletion capabilities (future enhancement)

---
