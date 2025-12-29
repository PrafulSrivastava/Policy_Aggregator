# Development Workflow

This section defines the development setup and workflow for the fullstack application, including local development environment, commands, and environment configuration.

### Local Development Setup

#### Prerequisites

Before starting development, ensure you have the following installed:

```bash
# Python 3.10 or higher
python --version  # Should be 3.10+

# PostgreSQL 14 or higher (or use Docker)
psql --version  # Should be 14+

# Git
git --version

# Optional but recommended:
# - Docker and Docker Compose (for local PostgreSQL)
# - Node.js 18+ (for Tailwind CSS compilation, if not using CDN)
```

**Installation Guides:**
- **Python:** https://www.python.org/downloads/
- **PostgreSQL:** https://www.postgresql.org/download/ or use Docker: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:14`
- **Git:** https://git-scm.com/downloads

#### Initial Setup

**1. Clone the repository:**
```bash
git clone https://github.com/your-org/policy-aggregator.git
cd policy-aggregator
```

**2. Create Python virtual environment:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

**3. Install Python dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Set up environment variables:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local configuration
# At minimum, set DATABASE_URL and JWT_SECRET_KEY
```

**5. Set up database:**
```bash
# Create database (if not using Docker)
createdb policy_aggregator

# Run migrations
alembic upgrade head

# Create initial admin user
python scripts/create_admin_user.py
```

**6. Compile Tailwind CSS (if using local build):**
```bash
# Install Tailwind CLI (if not using CDN)
npm install -D tailwindcss
npx tailwindcss -i ./admin-ui/static/css/input.css -o ./admin-ui/static/css/main.css --watch
```

#### Development Commands

**Start development server:**
```bash
# Start FastAPI development server with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or use FastAPI CLI
fastapi dev api/main.py
```

**Run tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov=fetchers --cov-report=html

# Run specific test file
pytest tests/unit/test_change_detector.py

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v
```

**Database migrations:**
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

**Manual pipeline execution:**
```bash
# Run fetch pipeline manually (for testing)
python scripts/run_fetch_pipeline.py

# Trigger specific source fetch
python scripts/run_fetch_pipeline.py --source-id <uuid>
```

**Code quality:**
```bash
# Format code with black
black api/ fetchers/ tests/

# Lint with flake8
flake8 api/ fetchers/ tests/

# Type checking with mypy (optional)
mypy api/
```

**Development workflow:**
```bash
# 1. Start PostgreSQL (if using Docker)
docker-compose up -d postgres

# 2. Start development server
uvicorn api.main:app --reload

# 3. In another terminal, watch Tailwind CSS (if using local build)
npx tailwindcss -i ./admin-ui/static/css/input.css -o ./admin-ui/static/css/main.css --watch

# Application available at http://localhost:8000
# API docs at http://localhost:8000/docs
# Admin UI at http://localhost:8000/
```

### Environment Configuration

#### Required Environment Variables

All configuration is managed via environment variables. The `.env` file (not committed to git) contains sensitive values.

**Backend Environment Variables (`.env`):**

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/policy_aggregator
# Or for async SQLAlchemy:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/policy_aggregator

# Authentication
JWT_SECRET_KEY=your-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Email Service (Resend)
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=alerts@policyaggregator.com

# Application Configuration
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
DEBUG=true  # Enable debug mode (development only)

# Server Configuration
HOST=0.0.0.0
PORT=8000

# CORS (if needed for API access)
ALLOWED_ORIGINS=http://localhost:8000,http://localhost:3000
```

**Frontend Environment Variables:**

Since we're using server-side rendering, frontend doesn't need separate environment variables. All configuration comes from the backend API.

**Shared/Development Variables:**

```bash
# Development Tools
PYTHONPATH=.  # Add project root to Python path

# Testing
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/policy_aggregator_test
```

#### Environment-Specific Configuration

**Development (`.env`):**
- `ENVIRONMENT=development`
- `DEBUG=true`
- `LOG_LEVEL=DEBUG`
- Local PostgreSQL database
- Resend test API key

**Staging (`.env.staging`):**
- `ENVIRONMENT=staging`
- `DEBUG=false`
- `LOG_LEVEL=INFO`
- Staging database URL
- Resend production API key

**Production (set in Railway/Render):**
- `ENVIRONMENT=production`
- `DEBUG=false`
- `LOG_LEVEL=WARNING`
- Production database URL
- Resend production API key
- Strong JWT secret key

#### Configuration Management

**Loading Environment Variables:**

```python
# api/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    # Email
    resend_api_key: str
    resend_from_email: str
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**Usage in Application:**

```python
from api.config import settings

# Access configuration
db_url = settings.database_url
secret_key = settings.jwt_secret_key
```

### Development Best Practices

**1. Code Organization:**
- Follow existing directory structure
- Keep functions small and focused
- Use type hints for all functions
- Document complex logic with docstrings

**2. Testing:**
- Write tests for new features
- Run tests before committing
- Aim for >80% code coverage on critical paths
- Use fixtures for test data

**3. Database:**
- Always create migrations for schema changes
- Test migrations up and down
- Never modify existing migrations (create new ones)
- Use transactions for data migrations

**4. Git Workflow:**
- Create feature branches: `git checkout -b feature/description`
- Commit frequently with clear messages
- Run tests and linting before pushing
- Create pull requests for review

**5. Debugging:**
- Use FastAPI's automatic API documentation at `/docs`
- Enable debug logging: `LOG_LEVEL=DEBUG`
- Use Python debugger: `import pdb; pdb.set_trace()`
- Check application logs in Railway dashboard (production)

### Hot Reload and Development Server

FastAPI's `--reload` flag enables automatic server restart on code changes:

```bash
uvicorn api.main:app --reload
```

**What auto-reloads:**
- Python code changes (`.py` files)
- FastAPI route changes
- Service and repository changes

**What requires manual restart:**
- Environment variable changes (`.env` file)
- Database schema changes (run migrations)
- Configuration file changes

**Template changes (Jinja2):**
- Templates auto-reload in development mode
- Static file changes (CSS/JS) may require browser refresh

### Database Development Workflow

**1. Make schema changes in SQLAlchemy models:**
```python
# api/models/db/source.py
class Source(Base):
    # Add new column
    new_field = Column(String(100), nullable=True)
```

**2. Generate migration:**
```bash
alembic revision --autogenerate -m "add new_field to sources"
```

**3. Review generated migration:**
```python
# alembic/versions/xxx_add_new_field_to_sources.py
# Review and adjust if needed
```

**4. Apply migration:**
```bash
alembic upgrade head
```

**5. Test rollback:**
```bash
alembic downgrade -1
alembic upgrade head
```

### Testing Workflow

**Run tests during development:**
```bash
# Watch mode (if using pytest-watch)
ptw

# Run tests on file change
pytest-watch

# Run specific test
pytest tests/unit/test_change_detector.py::test_hash_comparison
```

**Test database setup:**
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.database import Base

@pytest.fixture
def test_db():
    engine = create_engine("postgresql://.../test_db")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
```

### Common Development Tasks

**Add a new source fetcher:**
1. Create file: `fetchers/de_new_source.py`
2. Implement `fetch()` function following base interface
3. Test manually: `python scripts/run_fetch_pipeline.py --source-id <id>`
4. Add to source configuration via admin UI

**Add a new API endpoint:**
1. Add route in `api/routes/api.py`
2. Create Pydantic schemas in `api/models/schemas/`
3. Add service method in `api/services/`
4. Add repository method if needed
5. Write tests in `tests/integration/test_api/`
6. Test via `/docs` or admin UI

**Modify database schema:**
1. Update SQLAlchemy model
2. Generate migration: `alembic revision --autogenerate`
3. Review and test migration
4. Apply: `alembic upgrade head`
5. Update repository methods if needed
6. Update tests

---
