# ✅ Database Setup Complete!

## Current Status

✅ **PostgreSQL Database**: Running in Docker  
✅ **Database Name**: `policy_aggregator`  
✅ **Migrations**: Applied successfully  
✅ **Tables Created**: All 6 tables exist

## Database Tables

- ✅ `alembic_version` - Migration tracking
- ✅ `sources` - Policy source configurations
- ✅ `policy_versions` - Stored policy content versions
- ✅ `policy_changes` - Detected policy changes
- ✅ `route_subscriptions` - User route subscriptions
- ✅ `users` - User accounts

## Connection Details

**Docker Container:**
- Name: `policy-aggregator-db`
- Status: Running
- Port: `5432`
- Database: `policy_aggregator`
- User: `postgres`
- Password: `postgres`

**Connection String:**
```
postgresql://postgres:postgres@localhost:5432/policy_aggregator
```

## Next Steps

### 1. Create Admin User (if not done)

```powershell
# Set environment variables
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/policy_aggregator"
$env:JWT_SECRET_KEY="your-secret-key"

# Create admin user
python -m scripts.create_admin_user admin yourpassword
```

### 2. Start the Application

```powershell
# Make sure .env file has correct DATABASE_URL
uvicorn api.main:app --reload
```

### 3. Verify Everything Works

Visit: http://localhost:8000/health

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "..."
}
```

### 4. Login to Admin UI

Visit: http://localhost:8000  
Login with the admin credentials you created.

## Useful Commands

### Check Database Status
```powershell
docker ps --filter "name=policy-aggregator-db"
```

### View Tables
```powershell
docker exec policy-aggregator-db psql -U postgres -d policy_aggregator -c "\dt"
```

### Check Migration Status
```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/policy_aggregator"
$env:JWT_SECRET_KEY="temp-key"
alembic current
```

### Run New Migrations
```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/policy_aggregator"
$env:JWT_SECRET_KEY="temp-key"
alembic upgrade head
```

### Access PostgreSQL Shell
```powershell
docker exec -it policy-aggregator-db psql -U postgres -d policy_aggregator
```

## Troubleshooting

### Application Can't Connect
1. Check Docker container is running: `docker ps`
2. Verify `.env` file has correct `DATABASE_URL`
3. Test connection: `python -c "from api.database import init_db; init_db()"`

### Need to Reset Database
```powershell
# Stop container
docker stop policy-aggregator-db

# Remove container
docker rm policy-aggregator-db

# Recreate and setup
docker run --name policy-aggregator-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=policy_aggregator -p 5432:5432 -d postgres:14

# Wait a few seconds, then run migrations
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/policy_aggregator"
$env:JWT_SECRET_KEY="temp-key"
alembic upgrade head
```

---

**Your database is ready to use!** 🎉

