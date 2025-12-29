# User Interface Design Goals

### Overall UX Vision

The MVP prioritizes functionality and trust over visual polish. The admin interface is a simple, utilitarian tool for managing route subscriptions and monitoring system health. The primary user experience is email-based: alerts arrive in inboxes with clear, actionable information. The admin UI supports configuration and verification, not daily interaction. Users should feel confident that the system is monitoring reliably, not impressed by design sophistication.

**Key Principle:** "Boring is good" — simplicity builds trust faster than flashy features. The interface should feel professional and reliable, not experimental.

### Key Interaction Paradigms

1. **Email-First Workflow:** Primary interaction is via email alerts. Users don't need to log in daily; the system proactively notifies them.
2. **Configuration Over Interaction:** Admin UI is for setup and occasional verification, not continuous monitoring.
3. **Source Transparency:** Every screen shows exactly what sources are monitored and when they were last checked (builds trust).
4. **Diff-Centric Viewing:** When viewing changes, raw text diffs are acceptable — clarity over prettiness.
5. **Single-User Admin:** No multi-user complexity; one admin manages all subscriptions.

### Core Screens and Views

1. **Admin Login/Authentication Screen**
   - Simple authentication for single admin user
   - Basic security (password or simple auth)

2. **Dashboard/Home Screen**
   - Overview of active route subscriptions
   - Recent change detections (last 7-30 days)
   - System health indicators (last check timestamps per source)
   - Quick stats: total routes monitored, sources active, changes detected this month

3. **Route Subscription Management Screen**
   - List of active route subscriptions (origin → destination, visa type)
   - Add new route subscription (form: origin country, destination country, visa type)
   - View/edit/delete existing subscriptions
   - Show associated sources for each route

4. **Source Configuration Screen**
   - List of all configured sources with metadata
   - Add new source (form: country, visa type, URL, fetch type, check frequency)
   - Edit source configuration
   - View source status (last checked, last change detected, fetch errors)

5. **Change History View**
   - Chronological list of all detected changes
   - Filter by route, source, date range
   - Click to view full diff (raw text diff display)
   - Show: route, source, timestamp, change summary

6. **Change Detail/Diff View**
   - Full text diff showing what changed
   - Previous version vs. new version
   - Source attribution and timestamp
   - Link to original source URL
   - Raw text format acceptable (no fancy rendering needed)

7. **Manual Trigger/Testing Screen**
   - Button to manually trigger fetch for a specific source
   - View fetch results and logs
   - Testing/debugging tool for admin

### Accessibility: None

**Rationale:** MVP focuses on core functionality. Accessibility can be added later if needed. The admin interface is used by a single technical user, not a public-facing application.

### Branding

No specific branding requirements for MVP. Use a clean, professional, neutral design. Avoid experimental or playful elements. Prefer:
- Simple, readable typography
- Neutral color scheme (grays, blues)
- Minimal visual elements
- Focus on information clarity

**Assumption:** Branding can be refined after validating product-market fit with paying customers.

### Target Device and Platforms: Web Responsive

**Rationale:** Admin interface is web-based, accessible from desktop or laptop. Responsive design ensures usability on tablets if needed. No mobile app required (explicitly cut from MVP). Email alerts work on any device with email access.

---
