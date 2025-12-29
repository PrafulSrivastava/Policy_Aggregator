# Database Schema

This section transforms the conceptual data models into concrete PostgreSQL database schemas with DDL statements, indexes, constraints, and relationships.

### Schema Overview

The database uses PostgreSQL 14+ with the following characteristics:
- **Primary Keys:** UUID (using `gen_random_uuid()`)
- **Timestamps:** `TIMESTAMP WITH TIME ZONE` (stored in UTC)
- **JSON Fields:** JSONB for flexible metadata storage
- **Constraints:** Foreign keys, check constraints, unique constraints
- **Indexes:** Optimized for common query patterns

### Table Definitions

#### Sources Table

Stores configuration for government policy sources.

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country VARCHAR(2) NOT NULL,
    visa_type VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    fetch_type VARCHAR(10) NOT NULL CHECK (fetch_type IN ('html', 'pdf')),
    check_frequency VARCHAR(20) NOT NULL CHECK (check_frequency IN ('daily', 'weekly', 'custom')),
    name VARCHAR(255) NOT NULL,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    last_change_detected_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT sources_url_unique UNIQUE (url, country, visa_type)
);

-- Indexes
CREATE INDEX idx_sources_country_visa ON sources(country, visa_type);
CREATE INDEX idx_sources_is_active ON sources(is_active);
CREATE INDEX idx_sources_last_checked ON sources(last_checked_at);
CREATE INDEX idx_sources_metadata ON sources USING GIN (metadata);
```

**Key Design Decisions:**
- `country` as VARCHAR(2) for ISO country codes
- `fetch_type` and `check_frequency` use CHECK constraints for enum values
- `metadata` as JSONB for flexible source-specific configuration
- Unique constraint on `(url, country, visa_type)` prevents duplicate sources
- GIN index on `metadata` for efficient JSONB queries

#### Policy Versions Table

Stores immutable versions of policy content with versioning and hashing.

```sql
CREATE TABLE policy_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    content_hash VARCHAR(64) NOT NULL,
    raw_text TEXT NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE NOT NULL,
    normalized_at TIMESTAMP WITH TIME ZONE NOT NULL,
    content_length INTEGER NOT NULL,
    fetch_duration INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT policy_versions_hash_length CHECK (char_length(content_hash) = 64)
);

-- Indexes
CREATE INDEX idx_policy_versions_source_id ON policy_versions(source_id);
CREATE INDEX idx_policy_versions_content_hash ON policy_versions(content_hash);
CREATE INDEX idx_policy_versions_fetched_at ON policy_versions(fetched_at DESC);
CREATE INDEX idx_policy_versions_source_fetched ON policy_versions(source_id, fetched_at DESC);
```

**Key Design Decisions:**
- `content_hash` is VARCHAR(64) for SHA256 (64 hex characters)
- CHECK constraint ensures hash is correct length
- `raw_text` as TEXT (no size limit, but monitor growth)
- Index on `(source_id, fetched_at DESC)` for efficient "latest version" queries
- CASCADE delete: if source deleted, versions deleted (preserves referential integrity)

#### Policy Changes Table

Records detected changes between policy versions with diff text.

```sql
CREATE TABLE policy_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    old_hash VARCHAR(64) NOT NULL,
    new_hash VARCHAR(64) NOT NULL,
    diff TEXT NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    old_version_id UUID REFERENCES policy_versions(id) ON DELETE SET NULL,
    new_version_id UUID NOT NULL REFERENCES policy_versions(id) ON DELETE RESTRICT,
    diff_length INTEGER NOT NULL,
    alert_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT policy_changes_hash_length CHECK (
        char_length(old_hash) = 64 AND char_length(new_hash) = 64
    ),
    CONSTRAINT policy_changes_hash_different CHECK (old_hash != new_hash)
);

-- Indexes
CREATE INDEX idx_policy_changes_source_id ON policy_changes(source_id);
CREATE INDEX idx_policy_changes_detected_at ON policy_changes(detected_at DESC);
CREATE INDEX idx_policy_changes_old_hash ON policy_changes(old_hash);
CREATE INDEX idx_policy_changes_new_hash ON policy_changes(new_hash);
CREATE INDEX idx_policy_changes_source_detected ON policy_changes(source_id, detected_at DESC);
```

**Key Design Decisions:**
- Both `old_hash` and `new_hash` stored for flexibility and querying
- `diff` as TEXT (can be large for significant changes)
- `old_version_id` SET NULL on delete (old version might be deleted for cleanup)
- `new_version_id` RESTRICT on delete (new version must exist)
- CHECK constraint ensures hashes are different (data integrity)
- Index on `detected_at DESC` for chronological change history queries

#### Route Subscriptions Table

Stores user subscriptions to specific routes (origin → destination, visa type).

```sql
CREATE TABLE route_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_country VARCHAR(2) NOT NULL,
    destination_country VARCHAR(2) NOT NULL,
    visa_type VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT route_subscriptions_unique UNIQUE (origin_country, destination_country, visa_type, email),
    CONSTRAINT route_subscriptions_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes
CREATE INDEX idx_route_subscriptions_destination_visa ON route_subscriptions(destination_country, visa_type);
CREATE INDEX idx_route_subscriptions_is_active ON route_subscriptions(is_active);
CREATE INDEX idx_route_subscriptions_origin_destination_visa ON route_subscriptions(origin_country, destination_country, visa_type);
```

**Key Design Decisions:**
- Unique constraint on `(origin_country, destination_country, visa_type, email)` prevents duplicate subscriptions
- Email format validation via CHECK constraint (basic regex)
- Index on `(destination_country, visa_type)` for efficient route matching queries
- Composite index on all route fields for complete route lookups

#### Email Alerts Table

Tracks email alerts sent for policy changes (auditability and monitoring).

```sql
CREATE TABLE email_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_change_id UUID NOT NULL REFERENCES policy_changes(id) ON DELETE CASCADE,
    route_subscription_id UUID NOT NULL REFERENCES route_subscriptions(id) ON DELETE CASCADE,
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL,
    email_provider VARCHAR(50) NOT NULL DEFAULT 'resend',
    email_provider_id VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'sent' CHECK (status IN ('sent', 'failed', 'bounced')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_email_alerts_policy_change_id ON email_alerts(policy_change_id);
CREATE INDEX idx_email_alerts_route_subscription_id ON email_alerts(route_subscription_id);
CREATE INDEX idx_email_alerts_sent_at ON email_alerts(sent_at DESC);
CREATE INDEX idx_email_alerts_status ON email_alerts(status);
```

**Key Design Decisions:**
- `email_provider_id` nullable (may not be available for all providers)
- `status` with CHECK constraint for enum values
- CASCADE delete: if change or route deleted, alerts deleted (maintains referential integrity)
- Index on `status` for monitoring failed sends
- Index on `sent_at DESC` for chronological alert history

#### Users Table

Stores admin user accounts for authentication (single admin user for MVP).

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);
```

**Key Design Decisions:**
- `hashed_password` stores bcrypt hash (60 characters typical, 255 allows for future algorithms)
- `username` UNIQUE constraint for single admin user
- `last_login_at` for security monitoring (optional)
- Simple structure sufficient for MVP (can add roles/permissions later)

### Database Relationships Diagram

```
sources (1) ──< (many) policy_versions
sources (1) ──< (many) policy_changes
policy_versions (1) ──< (many) policy_changes (as old_version_id, nullable)
policy_versions (1) ──< (many) policy_changes (as new_version_id)
policy_changes (1) ──< (many) email_alerts
route_subscriptions (1) ──< (many) email_alerts
```

### Migration Strategy

**Tool:** Alembic (Python database migration tool, works with SQLAlchemy)

**Migration Files:**
- `alembic/versions/001_initial_schema.py` - Initial schema creation
- `alembic/versions/002_add_indexes.py` - Performance indexes
- Future migrations as schema evolves

**Migration Best Practices:**
- All migrations are reversible (up/down)
- Test migrations on development database first
- Backup production database before migrations
- Use transactions for migration safety

### Performance Considerations

**Index Strategy:**
- Indexes on foreign keys for JOIN performance
- Composite indexes for common query patterns (e.g., `(source_id, fetched_at DESC)`)
- GIN index on JSONB `metadata` field for flexible queries
- Indexes on frequently filtered columns (`is_active`, `status`, `detected_at`)

**Query Optimization:**
- Use `LIMIT` and `OFFSET` for pagination (consider cursor-based pagination for large datasets)
- Use `EXPLAIN ANALYZE` to optimize slow queries
- Monitor query performance and add indexes as needed

**Storage Considerations:**
- `raw_text` and `diff` fields can grow large (monitor table size)
- Consider archiving old policy versions if storage becomes an issue
- PostgreSQL TOAST (The Oversized-Attribute Storage Technique) handles large text automatically

### Data Integrity Constraints

1. **Foreign Key Constraints:** All relationships enforced at database level
2. **Check Constraints:** Enum values validated (fetch_type, check_frequency, status)
3. **Unique Constraints:** Prevent duplicate sources and route subscriptions
4. **NOT NULL Constraints:** Required fields enforced
5. **Hash Length Validation:** SHA256 hashes must be 64 characters

### Future Schema Evolution

The schema is designed to support future enhancements without breaking changes:

- **AI Summarization:** Add `summary` TEXT field to `policy_changes` table
- **Semantic Diffs:** Add `semantic_diff` JSONB field alongside `diff` TEXT
- **Multi-user Support:** Add `organization_id` to `route_subscriptions`, create `organizations` table
- **Webhook Notifications:** Create `webhook_subscriptions` table
- **Analytics:** Add `viewed_at` timestamp to `email_alerts` for open tracking

---
