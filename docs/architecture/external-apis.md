# External APIs

This section documents external service integrations required by the system. For MVP, the primary external integration is the Resend email service. Government sources are accessed via HTTP scraping rather than formal APIs.

### Resend API

**Purpose:** Transactional email delivery for policy change alerts. Sends email notifications to route subscribers when policy changes are detected.

**Documentation:** https://resend.com/docs

**Base URL(s):** 
- API: `https://api.resend.com`
- Webhook (optional): Configured webhook endpoint for delivery status

**Authentication:** 
- API Key authentication via `Authorization` header
- Format: `Bearer re_<api_key>`
- API key stored in environment variable: `RESEND_API_KEY`

**Rate Limits:**
- Free tier: 3,000 emails/month, 100 emails/day
- Paid tier: Based on plan (sufficient for MVP scale)
- No per-second rate limits for MVP scale

**Key Endpoints Used:**

- `POST /emails` - Send transactional email
  - **Request Body:**
    ```json
    {
      "from": "alerts@policyaggregator.com",
      "to": ["user@example.com"],
      "subject": "Policy Change Detected: India → Germany, Student Visa",
      "html": "<html>...</html>",
      "text": "Plain text version"
    }
    ```
  - **Response:**
    ```json
    {
      "id": "email_id_123",
      "from": "alerts@policyaggregator.com",
      "to": ["user@example.com"],
      "created_at": "2025-01-27T10:00:00Z"
    }
    ```
  - **Purpose:** Send policy change alert emails with route information, source name, timestamp, diff preview, and link to full diff

**Integration Notes:**
- **Email Templates:** Use Jinja2 templates for email content (HTML and plain text versions)
- **Error Handling:** Retry failed sends with exponential backoff (2-3 retries)
- **Delivery Tracking:** Store Resend email ID in `EmailAlert.emailProviderId` for tracking
- **Webhook Support:** Optional webhook for delivery status updates (bounce, delivery, open tracking)
- **Domain Verification:** Requires domain verification for production (e.g., `policyaggregator.com`)
- **From Address:** Must use verified domain email address (e.g., `alerts@policyaggregator.com`)

**Security Considerations:**
- API key stored as environment variable, never in code
- Use HTTPS for all API requests (enforced by Resend)
- Email content includes no sensitive data (only policy change information)
- Respect user email preferences (unsubscribe support can be added later)

**Cost:** Free tier sufficient for MVP (3,000 emails/month). Upgrade to paid tier if volume exceeds limits.

### Government Source Scraping

**Purpose:** Fetch policy content from official government websites. Sources are accessed via HTTP requests (HTML scraping or PDF download), not formal APIs.

**Note:** Government sources are not traditional APIs but external HTTP endpoints that require scraping. Each source has unique characteristics and is handled by a dedicated fetcher plugin.

**Common Patterns:**

1. **HTML Sources:**
   - Accessed via HTTP GET requests
   - Content extracted using BeautifulSoup
   - May require specific headers (User-Agent, Accept)
   - Some sources may require session handling or cookies

2. **PDF Sources:**
   - Accessed via HTTP GET requests (direct PDF URLs)
   - Content extracted using `pdftotext` or `pdfplumber`
   - May require specific headers for PDF download

**Authentication:** 
- Most government sources: None (public websites)
- Some sources: May require session cookies or basic auth (handled per-fetcher)

**Rate Limits:**
- Varies by source (typically no formal limits, but respectful scraping required)
- **Best Practice:** 
  - Respect `robots.txt` (FR18)
  - Use reasonable delays between requests (1-2 seconds)
  - Set appropriate User-Agent header
  - Don't overwhelm servers with rapid requests

**Key Sources (India → Germany Route, MVP):**

1. **Germany BMI (Federal Office for Migration and Refugees) - Student Visa**
   - **URL Pattern:** `https://www.bamf.de/...` (specific URLs to be determined)
   - **Type:** HTML or PDF
   - **Fetcher:** `fetchers/de_bmi_student.py`
   - **Notes:** Official German immigration authority

2. **Germany BMI - Work Visa**
   - **URL Pattern:** `https://www.bamf.de/...` (specific URLs to be determined)
   - **Type:** HTML or PDF
   - **Fetcher:** `fetchers/de_bmi_work.py`
   - **Notes:** Official German immigration authority

3. **Additional Sources (3-5 total for MVP)**
   - Specific URLs and fetchers to be determined during implementation
   - Each source will have dedicated fetcher plugin

**Integration Notes:**
- **Error Handling:** Each fetcher handles source-specific errors (404, timeout, parsing errors)
- **Retry Logic:** Failed fetches retried 2-3 times with exponential backoff (FR17)
- **Respect robots.txt:** Check and respect `robots.txt` before scraping (FR18)
- **User-Agent:** Set descriptive User-Agent header (e.g., "PolicyAggregator/1.0")
- **Timeout:** HTTP requests timeout after 30 seconds
- **Content Validation:** Verify fetched content is valid (non-empty, expected format)

**Security Considerations:**
- No authentication credentials stored in code (use environment variables if needed)
- HTTPS only for all source requests
- Validate and sanitize fetched content before storage
- Respect source terms of service and usage policies

**Legal Considerations:**
- Only scrape publicly available policy documents
- Respect copyright and terms of service
- Include clear disclaimers that content is for informational purposes (NFR10)
- No automated form submission or authentication bypass

### GitHub Actions API (Infrastructure)

**Purpose:** GitHub Actions is used for scheduled cron jobs (daily fetch pipeline). While not a direct API integration in the application code, it's part of the external infrastructure.

**Documentation:** https://docs.github.com/en/actions

**Usage:**
- Scheduled workflows (cron syntax) trigger daily fetch pipeline
- Workflow file: `.github/workflows/daily-fetch.yml`
- Executes Python script that runs fetch pipeline
- No API calls needed from application (GitHub Actions calls the application)

**Rate Limits:** 
- Free tier: 2,000 minutes/month (sufficient for daily cron jobs)
- No per-workflow rate limits

**Integration Notes:**
- Workflow triggered by cron schedule (e.g., `0 2 * * *` for 2 AM UTC daily)
- Workflow can call application endpoint or execute script directly
- Error notifications can be sent via GitHub Actions notifications or email

### Summary

**External Integrations Required:**
1. **Resend API** - Email delivery (primary external API)
2. **Government Sources** - HTTP scraping (not formal APIs, handled by fetcher plugins)
3. **GitHub Actions** - Infrastructure for scheduling (not application API)

**No External APIs Needed For:**
- Database (Railway managed PostgreSQL)
- Authentication (self-hosted JWT)
- File storage (content stored in database)
- CDN (static assets served directly)
- Monitoring (basic logging sufficient for MVP)

**Future External API Considerations:**
- Webhook endpoints for third-party integrations (post-MVP)
- API access for customers (post-MVP)
- Monitoring/APM services (Sentry, DataDog) if needed

---
