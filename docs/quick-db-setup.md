# Quick Database Setup Guide

## 🚀 Quick Start (Choose One Option)

### Option 1: Docker (Easiest - Recommended)

```powershell
# Run PostgreSQL in Docker
docker run --name policy-aggregator-db `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=policy_aggregator `
  -p 5432:5432 `
  -d postgres:14

# Verify it's running
docker ps
```

**Update your `.env` file:**
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/policy_aggregator
```

**Run migrations:**
```powershell
alembic upgrade head
```

**Create admin user:**
```powershell
python scripts/create_admin_user.py admin yourpassword
```

**Done!** ✅

---

### Option 2: Local PostgreSQL Installation

#### Step 1: Install PostgreSQL
1. Download from: https://www.postgresql.org/download/windows/
2. Install with default settings
3. **Remember the password** you set for `postgres` user

#### Step 2: Create Database
```powershell
# Connect to PostgreSQL
psql -U postgres

# In psql, run:
CREATE DATABASE policy_aggregator;
\q
```

#### Step 3: Update .env File
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/policy_aggregator
```

#### Step 4: Run Migrations
```powershell
alembic upgrade head
```

#### Step 5: Create Admin User
```powershell
python scripts/create_admin_user.py admin yourpassword
```

---

### Option 3: Railway (Cloud Database)

1. Sign up at https://railway.app
2. Create new project → Add PostgreSQL service
3. Copy the connection string from Railway dashboard
4. Update `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@host:port/database
   ```
5. Run migrations:
   ```powershell
   alembic upgrade head
   ```

---

## ✅ Verification Steps

### 1. Test Database Connection
```powershell
python -c "from api.database import init_db; init_db(); print('✅ Database connected!')"
```

### 2. Check Tables Created
```powershell
# If using Docker
docker exec -it policy-aggregator-db psql -U postgres -d policy_aggregator -c "\dt"

# If using local PostgreSQL
psql -U postgres -d policy_aggregator -c "\dt"
```

You should see tables:
- `sources`
- `policy_versions`
- `policy_changes`
- `route_subscriptions`
- `users`
- `email_alerts`

### 3. Start the Application
```powershell
uvicorn api.main:app --reload
```

Visit: http://localhost:8000/health

Should return: `{"status": "healthy", "database": "connected", ...}`

---

## 🔧 Troubleshooting

### "password authentication failed"
- Check your `.env` file has the correct password
- Verify PostgreSQL is running: `Get-Service postgresql*`

### "database does not exist"
- Create it: `CREATE DATABASE policy_aggregator;`

### "could not connect to server"
- Start PostgreSQL service: `Start-Service postgresql-x64-14`
- Check if port 5432 is in use: `netstat -an | findstr 5432`

### Migration Errors
- Reset database (⚠️ **WARNING**: Deletes all data):
  ```sql
  DROP DATABASE policy_aggregator;
  CREATE DATABASE policy_aggregator;
  ```
  Then: `alembic upgrade head`

---

## 📝 Current .env Configuration

Your current `.env` file has:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/policy_aggregator
```

**Make sure:**
1. PostgreSQL is running on port 5432
2. Password matches your PostgreSQL installation
3. Database `policy_aggregator` exists

---

## 🎯 Next Steps After Setup

1. ✅ Database is created
2. ✅ Migrations are run
3. ✅ Admin user is created
4. 🚀 Start developing!

For detailed instructions, see: [docs/setup-postgres.md](setup-postgres.md)

