# Requirements

### Functional

**FR1:** The system must support route-scoped monitoring where users can subscribe to specific origin country, destination country, and visa type combinations (e.g., India → Germany, Student visa).

**FR2:** The system must allow manual configuration of route subscriptions per organization/client (acceptable for MVP: one admin user managing subscriptions).

**FR3:** The system must fetch policy content from 3-5 official government sources per route (India → Germany route initially).

**FR4:** The system must store and track authoritative sources with metadata including: source ID, country, visa type, URL, fetch type, and check frequency.

**FR5:** The system must display explicit list of monitored sources for each route subscription.

**FR6:** The system must record and display "Last checked at: YYYY-MM-DD HH:MM" timestamp for each source.

**FR7:** The system must store versioned policy documents with content hash (SHA256), raw text, and fetched_at timestamp.

**FR8:** The system must detect changes by comparing content hashes between consecutive fetches of the same source.

**FR9:** The system must generate text diffs showing what changed compared to the previous version when a change is detected.

**FR10:** The system must store policy changes with: source_id, old_hash, new_hash, diff text, and detected_at timestamp.

**FR11:** The system must send proactive email alerts immediately when a policy change is detected for a subscribed route.

**FR12:** Email alerts must include: route (origin → destination, visa type), source name, detected timestamp, diff preview, and link to full diff.

**FR13:** The system must run automated daily checks of all configured sources (via cron job or scheduled task).

**FR14:** The system must support plugin-based source fetchers (one Python file per source) that can fetch HTML content (via Requests + BeautifulSoup) and PDF content (via pdftotext).

**FR15:** The system must normalize fetched content by stripping boilerplate, normalizing whitespace, and removing timestamps/logos where possible (without semantic parsing).

**FR16:** The system must provide a simple admin interface (single user) for: route subscription management, source configuration, viewing change history, and manual trigger for testing.

**FR17:** The system must handle fetch errors gracefully with retry logic and error notifications.

**FR18:** The system must respect robots.txt and terms of service when scraping public sources.

### Non Functional

**NFR1:** Infrastructure costs must stay under €50/month total (hosting: €10-20, database: €0-15, email: €0-20, scraping: free).

**NFR2:** Email delivery reliability must be >99% (transactional email service with monitoring).

**NFR3:** Change detection must have zero false positives (conservative normalization, manual review initially if needed).

**NFR4:** The system must use versioned policy storage with immutable history (no overwrites of previous versions).

**NFR5:** The system must use PostgreSQL database (Supabase/Railway/Neon) with JSON fields for flexibility.

**NFR6:** The system must use deterministic hashing (SHA256) for change detection (no AI-based change detection in MVP).

**NFR7:** The system must complete daily checks within reasonable time windows (avoid blocking or timeout issues).

**NFR8:** The system must log all fetch operations, change detections, and alert sends for auditability.

**NFR9:** The system must collect minimal user data (only route subscriptions, email addresses for alerts).

**NFR10:** The system must include clear disclaimers that this provides information, not legal advice.

**NFR11:** The system must be deployable via simple infrastructure (GitHub Actions for cron, or cheap VPS).

**NFR12:** The system architecture must allow adding new sources by creating new fetcher files without modifying core pipeline code.

**NFR13:** The system must support future upgrade paths (adding AI summarization, semantic diffs) without requiring core data model changes.

---
