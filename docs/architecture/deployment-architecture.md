# Deployment Architecture

This section defines the deployment strategy based on the Railway platform choice. The monolithic application (frontend + backend) is deployed as a single unit.

### Deployment Strategy

**Unified Deployment (Frontend + Backend):**

Since the application uses server-side rendering with Jinja2 templates, the frontend and backend are deployed together as a single FastAPI application. There is no separate frontend build or deployment step.

**Platform:** Railway

**Deployment Method:** Git-based deployment (connect Railway to GitHub repository)

**Build Command:** Railway auto-detects Python and installs dependencies from `requirements.txt`

**Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

**Output Directory:** N/A (server-side rendering, no static build output)

**CDN/Edge:** Not needed for MVP (static assets served directly from FastAPI)

**Database:** Railway PostgreSQL (managed, integrated with application)

**Key Deployment Steps:**

1. **Connect Repository:** Link Railway project to GitHub repository
2. **Configure Environment Variables:** Set all required env vars in Railway dashboard
3. **Deploy:** Railway automatically builds and deploys on git push to main branch
4. **Database Setup:** Railway creates PostgreSQL database, provides `DATABASE_URL`
5. **Run Migrations:** Execute `alembic upgrade head` on first deployment (via Railway CLI or script)

**Deployment Configuration:**

Railway uses `railway.json` or detects from project structure:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Alternative: Dockerfile Deployment**

If Railway's auto-detection doesn't work, use a Dockerfile:

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### CI/CD Pipeline

GitHub Actions provides continuous integration and deployment automation.

#### CI Pipeline (Continuous Integration)

Runs on every pull request and push to main branch:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: policy_aggregator_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run migrations
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/policy_aggregator_test
        run: |
          alembic upgrade head
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/policy_aggregator_test
        run: |
          pytest --cov=api --cov=fetchers --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
      
      - name: Lint with flake8
        run: |
          pip install flake8
          flake8 api/ fetchers/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 api/ fetchers/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

#### CD Pipeline (Continuous Deployment)

Deploys to Railway on push to main branch:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@v1.0.1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: policy-aggregator
          detach: false
      
      - name: Run migrations
        run: |
          railway run alembic upgrade head
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

**Alternative: Railway GitHub Integration**

Railway can auto-deploy from GitHub without GitHub Actions:
1. Connect Railway project to GitHub repository
2. Enable "Auto Deploy" in Railway settings
3. Railway automatically deploys on push to main branch
4. No GitHub Actions workflow needed

#### Scheduled Jobs Pipeline

Daily fetch pipeline runs via GitHub Actions cron:

```yaml
# .github/workflows/daily-fetch.yml
name: Daily Fetch Pipeline

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
  workflow_dispatch:  # Allow manual trigger

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run fetch pipeline
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
        run: |
          python scripts/run_fetch_pipeline.py
      
      - name: Notify on failure
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Daily fetch pipeline failed',
              body: 'The scheduled fetch pipeline encountered an error.'
            })
```

### Environments

The application supports three environments: Development (local), Staging (optional), and Production.

| Environment | Frontend URL | Backend URL | Database | Purpose |
|-------------|--------------|-------------|----------|---------|
| Development | `http://localhost:8000` | `http://localhost:8000/api` | Local PostgreSQL | Local development and testing |
| Staging | `https://policy-aggregator-staging.railway.app` | `https://policy-aggregator-staging.railway.app/api` | Railway PostgreSQL (staging) | Pre-production testing and validation |
| Production | `https://policy-aggregator.railway.app` | `https://policy-aggregator.railway.app/api` | Railway PostgreSQL (production) | Live environment for customers |

**Environment Configuration:**

**Development:**
- Runs locally on developer machine
- Uses local PostgreSQL database
- Debug mode enabled
- Detailed logging
- Test API keys

**Staging (Optional):**
- Separate Railway project for staging
- Staging database (can be reset/tested)
- Production-like configuration
- Used for final testing before production deployment
- Can be skipped for MVP if not needed

**Production:**
- Main Railway project
- Production database (backed up regularly)
- Debug mode disabled
- Production logging levels
- Production API keys and secrets
- HTTPS enabled (automatic with Railway)

**Environment Variable Management:**

- **Development:** `.env` file (not committed to git)
- **Staging/Production:** Set in Railway dashboard or via Railway CLI
- **Secrets:** All sensitive values stored in Railway's environment variables (encrypted)

**Deployment Workflow:**

1. **Development:** Developer works locally, tests changes
2. **Pull Request:** CI runs tests, validates code
3. **Merge to Main:** Triggers automatic deployment to Railway
4. **Production:** Railway deploys latest code, runs migrations if needed
5. **Verification:** Health check endpoint confirms deployment success

**Rollback Strategy:**

Railway provides deployment history and rollback:
- View previous deployments in Railway dashboard
- One-click rollback to previous deployment
- Database migrations can be rolled back: `alembic downgrade -1`

**Zero-Downtime Deployment:**

Railway handles zero-downtime deployments:
- New deployment starts before old one stops
- Health checks ensure new deployment is healthy
- Automatic rollback if health checks fail
- No manual intervention needed

---
