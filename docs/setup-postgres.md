# PostgreSQL Setup Guide

This guide will help you set up PostgreSQL for the Policy Aggregator project.

## Option 1: Install PostgreSQL Locally (Windows)

### Step 1: Download and Install PostgreSQL

1. **Download PostgreSQL 14+**:
   - Visit: https://www.postgresql.org/download/windows/
   - Or use the installer: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
   - Download PostgreSQL 14 or higher (15 or 16 recommended)

2. **Run the Installer**:
   - Run the downloaded `.exe` file
   - Follow the installation wizard
   - **Important**: Remember the password you set for the `postgres` superuser
   - Default port: `5432` (keep this unless you have a conflict)
   - Default installation directory: `C:\Program Files\PostgreSQL\{version}`

3. **Verify Installation**:
   ```powershell
   # Check if PostgreSQL service is running
   Get-Service postgresql*
   
   # Or check via psql
   psql --version
   ```

### Step 2: Create Database and User

1. **Open PostgreSQL Command Line**:
   - Open **pgAdmin 4** (installed with PostgreSQL) or
   - Open **Command Prompt** or **PowerShell** and navigate to PostgreSQL bin directory:
     ```powershell
     cd "C:\Program Files\PostgreSQL\{version}\bin"
     ```

2. **Connect to PostgreSQL**:
   ```powershell
   psql -U postgres
   ```
   Enter the password you set during installation.

3. **Create Database and User**:
   ```sql
   -- Create database
   CREATE DATABASE policy_aggregator;
   
   -- Create user (optional, you can use postgres user for development)
   CREATE USER policy_user WITH PASSWORD 'your_secure_password';
   
   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE policy_aggregator TO policy_user;
   
   -- Connect to the new database
   \c policy_aggregator
   
   -- Grant schema privileges (if using separate user)
   GRANT ALL ON SCHEMA public TO policy_user;
   
   -- Exit psql
   \q
   ```

### Step 3: Configure Environment Variables

1. **Create `.env` file** in the project root:
   ```powershell
   # Copy from example if it exists, or create new
   New-Item -Path .env -ItemType File
   ```

2. **Add Database Configuration** to `.env`:
   ```env
   # Database Configuration
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/policy_aggregator
   
   # Or if using separate user:
   # DATABASE_URL=postgresql://policy_user:your_secure_password@localhost:5432/policy_aggregator
   
   # JWT Authentication
   JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_HOURS=24
   
   # Application
   ENVIRONMENT=development
   LOG_LEVEL=INFO
   
   # Optional: Email Service
   RESEND_API_KEY=your_resend_api_key_here
   EMAIL_FROM_ADDRESS=alerts@policyaggregator.com
   ADMIN_UI_URL=http://localhost:9000
   ```

   **Note**: Replace `your_password` with the actual PostgreSQL password you set.

### Step 4: Run Database Migrations

1. **Install Dependencies** (if not already done):
   ```powershell
   pip install -r requirements.txt
   ```

2. **Run Migrations**:
   ```powershell
   alembic upgrade head
   ```

   This will create all the necessary tables in your database.

3. **Verify Tables Created**:
   ```powershell
   psql -U postgres -d policy_aggregator -c "\dt"
   ```

   You should see tables like:
   - `sources`
   - `policy_versions`
   - `policy_changes`
   - `route_subscriptions`
   - `users`
   - `email_alerts`

### Step 5: Create Admin User

```powershell
# Interactive mode (will prompt for username and password)
python scripts/create_admin_user.py

# Or provide credentials directly
python scripts/create_admin_user.py admin mypassword123
```

---

## Option 2: Use Docker (Recommended for Development)

### Step 1: Install Docker Desktop

1. Download Docker Desktop for Windows: https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop

### Step 2: Run PostgreSQL Container

```powershell
docker run --name policy-aggregator-db `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=policy_aggregator `
  -p 5432:5432 `
  -d postgres:14
```

### Step 3: Configure Environment Variables

Create `.env` file:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/policy_aggregator
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Step 4: Run Migrations

```powershell
alembic upgrade head
```

### Step 5: Create Admin User

```powershell
python scripts/create_admin_user.py admin mypassword123
```

### Useful Docker Commands

```powershell
# Stop container
docker stop policy-aggregator-db

# Start container
docker start policy-aggregator-db

# View logs
docker logs policy-aggregator-db

# Remove container (if needed)
docker rm -f policy-aggregator-db
```

---

## Option 3: Use Railway (Cloud Database)

1. **Sign up** at https://railway.app
2. **Create a new project**
3. **Add PostgreSQL service**
4. **Copy the connection string** from Railway dashboard
5. **Add to `.env`**:
   ```env
   DATABASE_URL=postgresql://user:password@host:port/database
   ```
6. **Run migrations**:
   ```powershell
   alembic upgrade head
   ```

---

## Troubleshooting

### Connection Issues

**Error: "password authentication failed"**
- Verify the password in your `.env` file matches the PostgreSQL password
- Try resetting the password:
  ```sql
  ALTER USER postgres WITH PASSWORD 'new_password';
  ```

**Error: "could not connect to server"**
- Check if PostgreSQL service is running:
  ```powershell
  Get-Service postgresql*
  ```
- Start the service if stopped:
  ```powershell
  Start-Service postgresql-x64-14  # Adjust version number
  ```

**Error: "database does not exist"**
- Create the database:
  ```sql
  CREATE DATABASE policy_aggregator;
  ```

### Port Conflicts

If port 5432 is already in use:
1. Change PostgreSQL port in `postgresql.conf`
2. Update `.env` with new port:
   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5433/policy_aggregator
   ```

### Migration Issues

**Error: "Target database is not up to date"**
- Check current migration version:
  ```powershell
  alembic current
  ```
- Upgrade to latest:
  ```powershell
  alembic upgrade head
  ```

**Error: "Can't locate revision identified by"**
- Reset database (⚠️ **WARNING**: This deletes all data):
  ```powershell
  # Drop and recreate database
  psql -U postgres -c "DROP DATABASE policy_aggregator;"
  psql -U postgres -c "CREATE DATABASE policy_aggregator;"
  alembic upgrade head
  ```

---

## Verify Setup

1. **Test Database Connection**:
   ```powershell
   python -c "from api.database import init_db; init_db(); print('Database connected successfully!')"
   ```

2. **Start the Application**:
   ```powershell
   uvicorn api.main:app --reload
   ```

3. **Check Health Endpoint**:
   - Open browser: http://localhost:8000/health
   - Should return: `{"status": "healthy", "database": "connected"}`

---

## Next Steps

After setting up PostgreSQL:
1. ✅ Database is created and migrations are run
2. ✅ Admin user is created
3. ✅ Application can connect to database
4. 🚀 Start developing!

For more information, see:
- [README.md](../README.md) - General setup instructions
- [docs/architecture/database-schema.md](../architecture/database-schema.md) - Database schema documentation

