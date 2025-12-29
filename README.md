# Policy Aggregator

A route-scoped regulatory change monitoring system that provides early warning with proof of monitoring (source attribution, timestamps, diffs) for immigration consultancies and global mobility teams.

## Overview

Policy Aggregator monitors official government policy sources for specific immigration routes (initially India → Germany, Student + Work visas) and alerts subscribers when policy changes are detected. The system provides:

- **Route-scoped monitoring**: Track policy changes for specific immigration routes
- **Authoritative source tracking**: Timestamps and source attribution for all policy versions
- **Change detection**: Automated detection of policy changes with diff generation
- **Proactive alerts**: Email notifications when changes are detected

## Project Structure

```
policy-aggregator/
├── api/                    # FastAPI backend application
├── admin-ui/               # Frontend templates and static assets (Jinja2)
├── fetchers/               # Plugin-based source fetchers
├── scripts/                # Utility scripts for development and operations
├── tests/                  # Test suite (unit, integration, fixtures)
├── docs/                   # Documentation (PRD, Architecture, Stories)
└── .github/workflows/      # CI/CD and scheduled jobs
```

For detailed project structure, see [docs/architecture/unified-project-structure.md](docs/architecture/unified-project-structure.md).

## Tech Stack

- **Backend**: Python 3.10+, FastAPI 0.104+, SQLAlchemy (async), PostgreSQL
- **Frontend**: Jinja2 templates, Tailwind CSS, vanilla JavaScript
- **Testing**: pytest 7.4+, pytest-asyncio
- **Database Migrations**: Alembic
- **CI/CD**: GitHub Actions

For complete tech stack details, see [docs/architecture/tech-stack.md](docs/architecture/tech-stack.md).

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 14+ (or use Railway managed database)
- Git

### Virtual Environment Setup

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your configuration:
   - `DATABASE_URL`: PostgreSQL connection string
   - `JWT_SECRET_KEY`: Secret key for JWT token generation
   - `RESEND_API_KEY`: API key for Resend email service (optional for development)

See `.env.example` for all required variables and documentation.

### Database Setup

1. Run database migrations:
   ```bash
   alembic upgrade head
   ```

2. Create an admin user:
   ```bash
   # Interactive mode (prompts for username and password)
   python scripts/create_admin_user.py
   
   # Or provide username and password as arguments
   python scripts/create_admin_user.py admin mypassword123
   
   # Or provide only username (will prompt for password)
   python scripts/create_admin_user.py admin
   ```

   **Note:** The script will validate that the username doesn't already exist and will hash the password using bcrypt before storing it in the database.

### Run Development Server

```bash
# Using uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python module
python -m uvicorn api.main:app --reload
```

The application will be available at:
- API: `http://localhost:8000`
- Health Check: `http://localhost:8000/health`
- API Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

**Note:** Make sure your `.env` file is configured with `DATABASE_URL` and other required environment variables before starting the server.

## Development Guidelines

### Coding Standards

- **Environment Variables**: Always access through config module, never use `os.getenv()` directly
- **Database Access**: Use Repository pattern, never write raw SQL
- **Error Handling**: Use FastAPI exception handlers, raise HTTPException or custom exceptions
- **Type Hints**: All Python functions must have type hints
- **Async/Await**: Use `async def` and `await` for all database operations and external API calls

For complete coding standards, see [docs/architecture/coding-standards.md](docs/architecture/coding-standards.md).

### File Naming Conventions

- **Python files**: `snake_case.py`
- **Test files**: `test_*.py` (pytest convention)
- **Templates**: `kebab-case.html`
- **JavaScript files**: `camelCase.js`

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov=fetchers

# Run specific test file
pytest tests/unit/test_change_detector.py
```

### Git Commit Standards

- Use present tense: "Add route subscription endpoint"
- Be descriptive: "Fix change detection for empty content"
- Reference issues: "Fix #123: Handle null previous_hash"

**Branch Naming:**
- Feature: `feature/add-route-subscription`
- Bugfix: `fix/change-detection-edge-case`
- Refactor: `refactor/normalize-content`

## Documentation

- **Product Requirements**: [docs/prd/](docs/prd/)
- **Architecture**: [docs/architecture/](docs/architecture/)
- **Stories**: [docs/stories/](docs/stories/)

## CI/CD

GitHub Actions workflows are configured in `.github/workflows/`:
- **ci.yml**: Continuous integration (runs tests on push and pull requests)
- **daily-fetch.yml**: Scheduled daily fetch pipeline (runs daily at 2 AM UTC)

### Daily Fetch Job Configuration

The daily fetch job runs automatically via GitHub Actions cron schedule. To configure it:

#### 1. Set Up GitHub Secrets

Navigate to your repository on GitHub:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add the following required secrets:

**Required Secrets:**
- `DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql://user:password@host:port/database`)
- `JWT_SECRET_KEY`: Secret key for JWT token generation (use a strong random string)

**Optional Secrets:**
- `RESEND_API_KEY`: API key for Resend email service (required if sending email alerts)
- `EMAIL_FROM_ADDRESS`: Email address to send alerts from (defaults to `alerts@policyaggregator.com`)
- `ADMIN_UI_URL`: Base URL for the admin UI (defaults to `http://localhost:8000`)
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins (defaults to `http://localhost:8000`)

#### 2. Modify Schedule (Optional)

To change when the job runs, edit `.github/workflows/daily-fetch.yml` and modify the cron expression:

```yaml
schedule:
  - cron: '0 2 * * *'  # Runs at 2 AM UTC daily
```

Cron syntax: `minute hour day month day-of-week`
- `0 2 * * *` = 2:00 AM UTC every day
- `0 0 * * *` = Midnight UTC every day
- `0 14 * * *` = 2:00 PM UTC every day

#### 3. Manual Trigger

You can manually trigger the workflow from the GitHub Actions UI:
1. Go to **Actions** tab in your repository
2. Select **Daily Fetch Job** workflow
3. Click **Run workflow** button
4. Select the branch and click **Run workflow**

#### 4. Monitoring

- Workflow runs are visible in the **Actions** tab
- Logs are available for each run
- Email notifications are sent to repository admins on failure (if enabled in repository settings)
- Check workflow logs for job execution details, including:
  - Sources processed
  - Changes detected
  - Alerts sent
  - Errors encountered

#### 5. Local Testing

You can test the daily fetch job locally:

```bash
# Set required environment variables
export DATABASE_URL="postgresql://user:password@host:port/database"
export JWT_SECRET_KEY="your-secret-key"

# Run the script
python scripts/run_daily_fetch_job.py
```

The script will:
- Initialize database connection
- Run the daily fetch job for all active sources with `check_frequency="daily"`
- Print a summary of results
- Exit with code 0 on success, 1 on failure

## License

[To be determined]

## Contributing

[To be determined]

---

For questions or issues, please refer to the documentation or create an issue in the repository.

