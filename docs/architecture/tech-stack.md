# Tech Stack

This is the DEFINITIVE technology selection for the entire project. All development must use these exact versions. This table is the single source of truth.

### Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|-----------|---------|---------|-----------|
| Frontend Language | HTML/CSS/JavaScript | Latest (ES2020+) | Client-side interactions and styling | Standard web technologies, no framework overhead for MVP |
| Frontend Framework | None (Server-Side Rendering) | N/A | Template rendering | Jinja2 templates with FastAPI, no SPA complexity needed |
| UI Component Library | Tailwind CSS | 3.x | Utility-first CSS framework | Minimal bundle size when purged, rapid development, aligns with "boring is good" principle |
| State Management | None (Server-Side State) | N/A | Application state | Server-rendered templates, state managed on backend |
| Backend Language | Python | 3.10+ | Core application logic | Single language for fetchers and API, excellent libraries for text processing |
| Backend Framework | FastAPI | 0.104+ | Web framework and API | Async support for concurrent fetches, built-in OpenAPI docs, simple deployment |
| API Style | REST | N/A | API architecture | Simple CRUD operations, JSON responses, FastAPI auto-generates OpenAPI spec |
| Database | PostgreSQL | 14+ | Data persistence | JSONB support for flexibility, versioned data model, Railway managed |
| Cache | None | N/A | Caching layer | Direct database queries for MVP, can add Redis later if needed |
| File Storage | None (Database Storage) | N/A | File storage | Policy content stored as text in database, no file storage needed |
| Authentication | bcrypt + FastAPI Security | Latest | Password hashing and auth | Simple password auth for single admin user, bcrypt for secure password hashing |
| Frontend Testing | Manual Testing | N/A | Frontend quality assurance | Admin UI is simple, manual testing sufficient for MVP |
| Backend Testing | pytest | 7.4+ | Backend unit and integration tests | Standard Python testing framework, excellent for FastAPI testing |
| E2E Testing | None | N/A | End-to-end testing | Can add Playwright/Cypress later if needed, not required for MVP |
| Build Tool | pip + requirements.txt | Latest | Dependency management | Standard Python package management, no build step needed |
| Bundler | None | N/A | Asset bundling | No frontend build needed for SSR, Tailwind CSS via CDN or simple build |
| IaC Tool | None (Railway Managed) | N/A | Infrastructure as code | Railway handles infrastructure, no IaC needed for MVP |
| CI/CD | GitHub Actions | Latest | Continuous integration | Free for public repos, runs tests and deploys to Railway |
| Monitoring | Python logging | Standard library | Application monitoring | Basic logging sufficient for MVP, can add Sentry/DataDog later |
| Logging | Python logging module | Standard library | Application logging | Structured logging to stdout, Railway captures logs |
| CSS Framework | Tailwind CSS | 3.x | Styling framework | Utility-first CSS, minimal customization, rapid development |

---
