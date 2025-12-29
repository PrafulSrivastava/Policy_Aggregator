# Unified Project Structure

This section defines the complete monorepo structure that accommodates both frontend (Jinja2 templates) and backend (FastAPI) in a single repository. The structure is simple and maintainable, without complex monorepo tooling for MVP.

### Complete Project Structure

```
policy-aggregator/
├── .github/                          # GitHub configuration
│   └── workflows/
│       ├── ci.yml                   # Continuous integration (tests)
│       └── daily-fetch.yml          # Scheduled daily fetch pipeline
├── alembic/                          # Database migrations
│   ├── versions/                    # Migration files
│   │   ├── 001_initial_schema.py
│   │   └── ...
│   ├── env.py                       # Alembic environment config
│   └── script.py.mako               # Migration template
├── api/                              # FastAPI backend application
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── database.py                  # Database connection and session
│   ├── config.py                    # Application configuration
│   ├── routes/                       # API and web routes
│   │   ├── __init__.py
│   │   ├── api.py                   # REST API endpoints (/api/*)
│   │   ├── web.py                   # Web page routes (HTML rendering)
│   │   ├── auth.py                  # Authentication routes
│   │   └── health.py                 # Health check endpoint
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── fetcher_manager.py       # Source fetcher orchestration
│   │   ├── normalizer.py            # Content normalization
│   │   ├── change_detector.py       # Change detection logic
│   │   ├── diff_generator.py       # Diff generation
│   │   ├── alert_engine.py          # Email alert sending
│   │   └── dashboard.py             # Dashboard statistics
│   ├── repositories/                 # Data access layer (Repository pattern)
│   │   ├── __init__.py
│   │   ├── source_repository.py
│   │   ├── policy_version_repository.py
│   │   ├── policy_change_repository.py
│   │   ├── route_subscription_repository.py
│   │   ├── email_alert_repository.py
│   │   └── user_repository.py
│   ├── models/                       # Data models
│   │   ├── __init__.py
│   │   ├── db/                      # SQLAlchemy database models
│   │   │   ├── __init__.py
│   │   │   ├── source.py
│   │   │   ├── policy_version.py
│   │   │   ├── policy_change.py
│   │   │   ├── route_subscription.py
│   │   │   ├── email_alert.py
│   │   │   └── user.py
│   │   └── schemas/                 # Pydantic request/response models
│   │       ├── __init__.py
│   │       ├── source.py
│   │       ├── policy_version.py
│   │       ├── policy_change.py
│   │       ├── route_subscription.py
│   │       └── user.py
│   ├── middleware/                   # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── auth.py                  # Authentication middleware
│   │   └── error_handler.py         # Global error handling
│   ├── auth/                         # Authentication utilities
│   │   ├── __init__.py
│   │   └── auth.py                  # JWT and password hashing
│   ├── utils/                        # Utility functions
│   │   ├── __init__.py
│   │   ├── hashing.py               # SHA256 hash utilities
│   │   └── logging.py                # Logging configuration
│   └── integrations/                 # External service integrations
│       ├── __init__.py
│       └── resend.py                 # Resend email API client
├── admin-ui/                         # Frontend (Jinja2 templates)
│   ├── templates/                    # Jinja2 templates
│   │   ├── base.html                 # Base template with layout
│   │   ├── components/               # Reusable component macros
│   │   │   ├── button.html
│   │   │   ├── form_input.html
│   │   │   ├── table.html
│   │   │   ├── modal.html
│   │   │   ├── status_indicator.html
│   │   │   └── alert.html
│   │   ├── pages/                   # Page templates
│   │   │   ├── login.html
│   │   │   ├── dashboard.html
│   │   │   ├── routes/
│   │   │   │   ├── list.html
│   │   │   │   └── form.html
│   │   │   ├── sources/
│   │   │   │   ├── list.html
│   │   │   │   ├── form.html
│   │   │   │   └── detail.html
│   │   │   ├── changes/
│   │   │   │   ├── list.html
│   │   │   │   └── detail.html
│   │   │   └── trigger.html
│   │   └── emails/                  # Email templates
│   │       └── change_alert.html
│   └── static/                      # Static assets
│       ├── css/
│       │   └── main.css             # Tailwind CSS (compiled)
│       └── js/
│           ├── main.js              # Main JavaScript
│           ├── api.js               # API client utilities
│           └── forms.js             # Form validation
├── fetchers/                         # Source fetcher plugins
│   ├── __init__.py
│   ├── base.py                      # Base fetcher interface
│   ├── de_bmi_student.py            # Germany BMI Student visa fetcher
│   ├── de_bmi_work.py               # Germany BMI Work visa fetcher
│   └── ...                          # Additional source fetchers
├── scripts/                          # Utility scripts
│   ├── create_admin_user.py         # Create initial admin user
│   ├── run_fetch_pipeline.py        # Manual fetch pipeline execution
│   └── seed_data.py                 # Seed test data (optional)
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest configuration and fixtures
│   ├── unit/                        # Unit tests
│   │   ├── test_services/
│   │   │   ├── test_change_detector.py
│   │   │   ├── test_normalizer.py
│   │   │   └── test_diff_generator.py
│   │   ├── test_repositories/
│   │   └── test_utils/
│   ├── integration/                 # Integration tests
│   │   ├── test_api/
│   │   │   ├── test_routes.py
│   │   │   ├── test_sources.py
│   │   │   └── test_changes.py
│   │   ├── test_fetchers/
│   │   └── test_pipeline/
│   └── fixtures/                    # Test data fixtures
│       └── sample_data.py
├── docs/                            # Documentation
│   ├── prd.md                       # Product Requirements Document
│   ├── architecture.md              # This document
│   ├── front-end-spec.md            # UI/UX specification
│   └── brainstorming-session-results.md
├── .env.example                     # Environment variable template
├── .gitignore                       # Git ignore rules
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Python project configuration (optional)
├── README.md                        # Project overview and setup
└── Dockerfile                       # Docker configuration (optional, for Railway)
```

### Key Directory Explanations

**`api/`** - FastAPI backend application
- **`routes/`**: HTTP route handlers (API endpoints and web pages)
- **`services/`**: Business logic layer (orchestrates repositories and external services)
- **`repositories/`**: Data access abstraction (Repository pattern)
- **`models/db/`**: SQLAlchemy ORM models (database schema)
- **`models/schemas/`**: Pydantic models (request/response validation)

**`admin-ui/`** - Frontend templates and static assets
- **`templates/`**: Jinja2 templates for server-side rendering
- **`static/`**: CSS (Tailwind) and JavaScript files

**`fetchers/`** - Plugin-based source fetchers
- Each source has its own Python file (plugin architecture)
- `base.py` defines the fetcher interface
- New sources added by creating new files (no core code changes)

**`scripts/`** - Utility scripts for development and operations
- Admin user creation, manual pipeline execution, data seeding

**`tests/`** - Test suite organization
- Unit tests for services, repositories, utilities
- Integration tests for API endpoints and full pipeline
- Fixtures for test data

### File Naming Conventions

- **Python files**: `snake_case.py`
- **Template files**: `kebab-case.html` (for consistency)
- **JavaScript files**: `camelCase.js` or `kebab-case.js`
- **Test files**: `test_*.py` (pytest convention)
- **Migration files**: `{revision}_{description}.py` (Alembic convention)

### Shared Code Organization

Since this is a monorepo without separate packages, shared code is organized as:

- **Shared types**: TypeScript interfaces would go in `api/models/schemas/` (Pydantic models serve similar purpose)
- **Shared utilities**: Common utilities in `api/utils/`
- **Shared constants**: Configuration in `api/config.py`

For MVP, no separate shared package needed. Can be refactored later if complexity grows.

### Environment Configuration

**`.env.example`** template includes:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/policy_aggregator

# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Email Service
RESEND_API_KEY=re_your_api_key_here

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Build and Deployment Files

- **`requirements.txt`**: Python dependencies (FastAPI, SQLAlchemy, etc.)
- **`Dockerfile`**: Optional, for containerized deployment to Railway
- **`.github/workflows/`**: CI/CD and scheduled jobs

### Monorepo Tooling

**MVP Approach:** No monorepo tooling (Nx, Turborepo, Lerna)
- Simple directory structure is sufficient
- Python virtual environment handles dependencies
- No build step needed (Jinja2 templates, static files)
- Can add monorepo tooling later if complexity grows

**Future Consideration:** If project grows to include:
- Separate frontend build (React/Next.js)
- Multiple backend services
- Shared TypeScript packages

Then consider adding:
- **Turborepo** for build orchestration
- **npm workspaces** or **pnpm workspaces** for package management
- **Shared TypeScript package** for type definitions

### Development Workflow Integration

This structure supports:
- **Local development**: Run FastAPI dev server, templates auto-reload
- **Testing**: Pytest discovers tests in `tests/` directory
- **Migrations**: Alembic manages database schema changes
- **CI/CD**: GitHub Actions runs tests and deploys
- **Scheduled jobs**: GitHub Actions cron triggers fetch pipeline

### Scalability Considerations

The structure can evolve to support:
- **Microservices**: Extract services to separate directories/packages
- **SPA Frontend**: Add `frontend/` directory with React/Next.js
- **API Gateway**: Add `gateway/` directory if needed
- **Shared Libraries**: Extract to `packages/` directory

For MVP, the simple structure is optimal - no premature optimization.

---
