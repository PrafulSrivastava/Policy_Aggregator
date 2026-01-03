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
- Docker and Docker Compose (for Docker-based deployment)

### Docker-Based Deployment (Recommended)

The easiest way to get started is using Docker Compose, which sets up the frontend (React), backend (FastAPI), and PostgreSQL database automatically.

#### Quick Start with Docker

1. **Create environment file:**
   
   Create a `.env` file in the project root with your configuration. All variables from `.env` are automatically loaded into Docker containers.
   
   **Quick setup:**
   ```bash
   # Copy the example file (env.example) to .env
   # Windows PowerShell:
   Copy-Item env.example .env
   
   # Linux/macOS:
   cp env.example .env
   
   # Then edit .env and update the values with your configuration
   ```
   
   **Required variables:**
   ```bash
   # Database Configuration
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=policy_aggregator
   POSTGRES_PORT=5432
   
   # Application - Database URL (will be overridden to use Docker service 'db')
   # You can set this for local development, but Docker Compose will override it
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/policy_aggregator
   
   # Application - Authentication
   JWT_SECRET_KEY=your-secret-key-change-in-production
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_HOURS=24
   
   # Application - General
   ENVIRONMENT=development
   LOG_LEVEL=INFO
   ADMIN_UI_URL=http://localhost:8000
   FRONTEND_URL=http://localhost:3000
   
   # Frontend - API URL (used at build time)
   # For production with nginx proxy, use empty string or relative path
   # For development, use http://localhost:8000
   VITE_API_BASE_URL=http://localhost:8000
   
   # Docker - Ports (optional, defaults shown)
   APP_PORT=8000
   FRONTEND_PORT=3000
   
   # Optional: Email service
   RESEND_API_KEY=
   EMAIL_FROM_ADDRESS=alerts@policyaggregator.com
   ADMIN_EMAIL=
   
   # Optional: Google OAuth
   GOOGLE_OAUTH_CLIENT_ID=
   GOOGLE_OAUTH_CLIENT_SECRET=
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/google/callback
   
   # Optional: CORS (comma-separated list)
   CORS_ORIGINS=http://localhost:8000,http://localhost:3000
   ```
   
   **How it works:**
   - **All variables from `.env` are automatically loaded** into Docker containers using `env_file` directive
   - No need to manually specify each variable in docker-compose.yml
   - The `DATABASE_URL` is automatically overridden in Docker to use `db` as the hostname (Docker service name) instead of localhost
   - The `VITE_API_BASE_URL` is passed as a build argument to the frontend container (Vite requires env vars at build time)
   - You only need to set variables you want to customize - defaults are provided for optional variables
   - Variables can be added/removed from `.env` without modifying docker-compose.yml

2. **Build and start containers:**
   ```bash
   docker-compose up -d
   ```

3. **Create admin user:**
   ```bash
   docker-compose exec app python scripts/create_admin_user.py admin
   ```

4. **Access the application:**
   - **Frontend (React)**: `http://localhost:3000`
   - **Backend API**: `http://localhost:8000`
   - **Health Check**: `http://localhost:8000/health`
   - **API Documentation**: `http://localhost:8000/docs`
   - **Admin UI (Jinja2)**: `http://localhost:8000`

#### Docker Commands

```bash
# Start all services (frontend, backend, database)
docker-compose up -d

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f app      # Backend
docker-compose logs -f frontend # Frontend
docker-compose logs -f db       # Database

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Rebuild after code changes
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build frontend

# Run database migrations manually
docker-compose exec app alembic upgrade head

# Access database shell
docker-compose exec db psql -U postgres -d policy_aggregator

# Run Python commands in container
docker-compose exec app python scripts/create_admin_user.py admin

# Access frontend container shell
docker-compose exec frontend sh
```

#### Development with Hot Reload

For development with automatic code reloading:

1. **Copy the override example:**
   ```bash
   cp docker-compose.override.yml.example docker-compose.override.yml
   ```

2. **Start with override:**
   ```bash
   docker-compose up
   ```

The override file mounts your source code as volumes, enabling hot reload for both backend and frontend when you make changes.

**Note:** In development mode with the override file:
- Backend runs with `--reload` flag for automatic restart on code changes
- Frontend uses Vite dev server with hot module replacement (HMR)
- Both services watch for file changes and reload automatically

#### Architecture Overview

The Docker setup includes three services:

1. **Frontend (React)**: 
   - Production: Built React app served via nginx on port 3000
   - Development: Vite dev server with HMR on port 3000
   - API calls are proxied through nginx to the backend in production

2. **Backend (FastAPI)**:
   - Runs on port 8000
   - Handles API requests, authentication, and serves Jinja2 admin UI
   - Connects to PostgreSQL database

3. **Database (PostgreSQL)**:
   - PostgreSQL 14 on port 5432
   - Persistent data stored in Docker volume

**Network Communication:**
- Frontend → Backend: In production, nginx proxies `/api/*` and `/auth/*` to backend
- Backend → Database: Direct connection using service name `db`
- All services are on the same Docker network for internal communication

#### Production Considerations

For production deployment:

1. **Use strong secrets:**
   - Generate a strong `JWT_SECRET_KEY` (e.g., using `openssl rand -hex 32`)
   - Use strong database passwords
   - Store secrets securely (use Docker secrets or environment variable management)

2. **Update CORS origins and URLs:**
   - Set `CORS_ORIGINS` to include your production frontend and backend domains
   - Update `ADMIN_UI_URL` to your production backend URL
   - Update `FRONTEND_URL` to your production frontend URL
   - Update `VITE_API_BASE_URL` to your production backend URL (or use nginx proxy)

3. **Configure reverse proxy and SSL:**
   - Use nginx or Traefik in front of both frontend and backend
   - Enable HTTPS/SSL certificates
   - Consider using Let's Encrypt for free SSL certificates

4. **Database backups:**
   - Set up regular backups of the `postgres_data` volume
   - Consider using managed database services for production
   - Test restore procedures regularly

5. **Frontend API Configuration:**
   - The nginx configuration already proxies `/api/*` and `/auth/*` to the backend
   - For production with nginx proxy, set `VITE_API_BASE_URL` to empty string or `/` in your `.env` file
   - This allows the frontend to use relative URLs which nginx will proxy to the backend
   - Example for production: `VITE_API_BASE_URL=`
   - For development without proxy: `VITE_API_BASE_URL=http://localhost:8000`

### Manual Setup (Without Docker)

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
   - `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth 2.0 Client ID (optional, for Google OAuth login)
   - `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth 2.0 Client Secret (optional, for Google OAuth login)
   - `GOOGLE_OAUTH_REDIRECT_URI`: Google OAuth redirect URI (e.g., `http://localhost:8000/auth/google/callback`)

See `.env.example` for all required variables and documentation.

### Google OAuth Setup (Optional)

To enable Google OAuth authentication:

1. **Create Google Cloud Console Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Configure OAuth Consent Screen:**
   - Go to **APIs & Services** → **OAuth consent screen**
   - Choose **External** user type (for testing) or **Internal** (for Google Workspace)
   - Fill in required fields (App name, User support email, Developer contact)
   - Add scopes: `openid`, `email`, `profile`

3. **Create OAuth 2.0 Credentials:**
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth client ID**
   - Choose **Web application**
   - Add authorized redirect URIs:
     - Development: `http://localhost:8000/auth/google/callback`
     - Production: `https://yourdomain.com/auth/google/callback`

4. **Add Credentials to `.env`:**
   ```
   GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/google/callback
   ```

5. **Run Database Migration:**
   ```bash
   alembic upgrade head
   ```

The "Sign in with Google" button will appear on the login page once OAuth credentials are configured.

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

