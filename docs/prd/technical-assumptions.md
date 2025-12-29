# Technical Assumptions

### Repository Structure: Monorepo

**Rationale:** Single repository for all components (source fetchers, admin API, admin UI, cron jobs). Simplifies deployment, versioning, and development. No need for microservices complexity at MVP stage.

**Assumption:** All code lives in one repo with clear directory structure (e.g., `fetchers/`, `api/`, `admin-ui/`, `scripts/`).

### Service Architecture: Monolith

**Rationale:** Single deployable application (API + admin UI) with scheduled background jobs. Avoids microservices overhead. The "plugin" architecture for fetchers is code organization, not service separation.

**Components:**
- Admin API (REST or simple web framework)
- Admin UI (served by same app or static files)
- Background job scheduler (cron or task queue)
- Source fetchers (Python modules, not separate services)

**Assumption:** Can be deployed as a single application to one hosting environment.

### Testing Requirements: Unit + Integration

**Rationale:** 
- Unit tests for core logic (hashing, diff generation, normalization)
- Integration tests for end-to-end pipeline (fetch → normalize → diff → alert)
- Manual testing convenience methods for source fetchers (test individual fetchers easily)

**What to test:**
- Change detection accuracy (no false positives)
- Email delivery
- Source fetcher reliability
- Data integrity (versioning, hashing)

**What can wait:**
- Full E2E UI tests (admin UI is simple)
- Performance/load testing (low traffic initially)

**Assumption:** Focus on correctness and reliability over comprehensive test coverage initially.

### Programming Language: Python

**Rationale:** 
- Source fetchers are Python (Requests, BeautifulSoup, pdftotext)
- Python ecosystem for web frameworks (FastAPI, Flask, Django)
- Single language simplifies development
- Good libraries for text processing and diffs

**Assumption:** Python 3.10+ for modern features and compatibility.

### Web Framework: FastAPI (Recommended)

**Rationale:**
- Lightweight, fast development
- Built-in API documentation
- Async support (useful for concurrent fetches)
- Simple deployment
- Good for admin API

**Alternative considered:** Flask (simpler, but FastAPI offers better async support for concurrent source fetching).

**Assumption:** FastAPI for admin API unless there's a strong preference for another framework.

### Admin UI Framework: Simple Template-Based (Recommended)

**Rationale:** 
- MVP UI can be "ugly" — focus on functionality
- Template-based (Jinja2 with FastAPI, or similar) is sufficient
- No need for React/Vue complexity
- Faster to build and deploy

**Alternative considered:** 
- React/Next.js (overkill for MVP)
- Plain HTML/JS (acceptable but template-based is cleaner)

**Assumption:** Server-rendered templates (Jinja2) unless there's a preference for a different approach.

### Database: PostgreSQL (Supabase/Railway/Neon)

**Rationale:**
- JSON fields for flexibility (source metadata, route configs)
- Easy indexing (sources, timestamps, routes)
- Cheap/free tiers available
- Reliable and well-supported
- Versioned data model fits relational structure

**Specific providers considered:**
- Supabase (Postgres + free tier, good DX)
- Railway (simple deployment, Postgres included)
- Neon (serverless Postgres, good for scaling)

**Assumption:** PostgreSQL with JSONB support. Provider choice can be made during setup.

### Source Fetching Libraries

**HTML Scraping:** `requests` + `beautifulsoup4`
- Standard Python libraries
- Handles most HTML sources
- Simple and reliable

**PDF Extraction:** `pdftotext` (via subprocess) or `PyPDF2`/`pdfplumber`
- Extract text from PDF policy documents
- `pdftotext` is simple and effective

**Assumption:** These libraries handle the initial 3-5 sources. If a source requires headless browser, we'll add Selenium/Playwright only if absolutely necessary.

### Change Detection: Python `difflib`

**Rationale:**
- Standard library (no dependencies)
- Deterministic text diff generation
- Sufficient for MVP (raw text diffs acceptable)
- Can upgrade to semantic diff later without changing core architecture

**Assumption:** `difflib.unified_diff()` or `difflib.HtmlDiff()` for generating diffs. Store raw diff text in database.

### Hashing: SHA256 (Python `hashlib`)

**Rationale:**
- Standard library
- Deterministic (same content = same hash)
- Fast comparison
- Secure and auditable

**Assumption:** SHA256 for content hashing. No need for cryptographic security, but SHA256 is standard and reliable.

### Scheduling/Background Jobs: GitHub Actions Cron (Recommended) or VPS Cron

**Rationale:**
- GitHub Actions: Free for public repos, scheduled workflows, no server management
- VPS Cron: More control, but requires server management (€10-20/month)

**Recommendation:** Start with GitHub Actions (free), migrate to VPS if needed for more control or private repos.

**Assumption:** Daily cron job triggers fetch pipeline. Can be upgraded to more frequent checks later.

### Email Service: Resend (Recommended) or AWS SES or Mailgun

**Rationale:**
- Resend: Modern API, good free tier, simple setup
- AWS SES: Very cheap, but more complex setup
- Mailgun: Reliable, good free tier

**Recommendation:** Resend for simplicity and developer experience.

**Assumption:** Transactional email only. No marketing emails. Simple templates (route, source, timestamp, diff preview, link).

### Deployment Target: Railway (Recommended) or Render or Fly.io

**Rationale:**
- Railway: Simple deployment, Postgres included, good free tier, easy scaling
- Render: Similar to Railway, good free tier
- Fly.io: Good for global distribution (not needed for MVP)

**Recommendation:** Railway for simplicity and integrated Postgres.

**Assumption:** Single region deployment (EU or US). No multi-region needed for MVP.

### Environment Variables / Configuration

**Required:**
- Database connection string
- Email service API key
- Admin authentication credentials
- Source URLs and configuration

**Assumption:** Use environment variables for all secrets and configuration. No hardcoded credentials.

### API Design: RESTful (Simple)

**Rationale:**
- Admin API for managing routes, sources, viewing changes
- Simple CRUD operations
- No complex API versioning needed for MVP

**Endpoints needed:**
- Routes: GET/POST/DELETE route subscriptions
- Sources: GET/POST/PUT sources
- Changes: GET changes (filtered by route, date)
- Health: GET system status

**Assumption:** RESTful API with JSON responses. FastAPI auto-generates OpenAPI docs.

### Authentication: Simple Password Auth (MVP)

**Rationale:**
- Single admin user (no multi-user complexity)
- Simple password authentication sufficient
- Can upgrade to proper auth system later

**Assumption:** Basic username/password authentication. Session-based or token-based (JWT). No OAuth/SSO needed for MVP.

### Logging: Python `logging` Module

**Rationale:**
- Standard library
- Log to files or stdout (captured by hosting platform)
- Structured logging for debugging

**Assumption:** Log all fetch operations, change detections, errors. Logs viewable via hosting platform dashboard or log files.

### Error Handling: Graceful Degradation

**Rationale:**
- If one source fails, continue with others
- Retry logic for transient failures
- Alert admin on persistent failures
- Never crash entire pipeline due to one source

**Assumption:** Retry failed fetches 2-3 times with exponential backoff. Log errors. Email admin on persistent failures.

### Additional Technical Assumptions and Requests

- **No AI/ML in MVP:** No LLM calls, no summarization, no semantic analysis. Pure deterministic text processing.
- **No Caching Layer:** Direct database queries. Can add caching later if performance becomes an issue.
- **No CDN:** Static assets served directly from application. No CDN needed for MVP.
- **No Load Balancer:** Single application instance. Can scale horizontally later if needed.
- **No Message Queue:** Direct function calls for pipeline. Can add queue (Redis/RabbitMQ) later for reliability.
- **No Monitoring/APM Initially:** Basic logging sufficient. Can add Sentry/DataDog later if needed.
- **Source Fetchers as Plugins:** Each source fetcher is a separate Python module/function. Easy to add new sources without modifying core code.
- **Normalization Pipeline:** Separate normalization step before hashing. Can be adjusted per source if needed.
- **Immutable Policy Versions:** Once stored, policy versions are never modified. Only new versions added.
- **UTC Timestamps:** All timestamps stored in UTC. Display in user's timezone if needed (future enhancement).

---
