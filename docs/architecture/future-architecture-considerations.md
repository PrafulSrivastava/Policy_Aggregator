# Future Architecture Considerations

This section addresses how the MVP architecture supports the planned future epics (Epic 5-8) detailed in the PRD. The architecture is designed to accommodate these enhancements without requiring fundamental restructuring.

### Epic 5: Route Expansion (v0.2) - Architecture Readiness

**Epic Summary:** Add 1-2 more routes and additional source fetchers after first paying customer validates the model.

**Architecture Support:**

✅ **Plugin Architecture Validated:** The plugin-based fetcher system (NFR12) is designed exactly for this - adding new routes requires only creating new fetcher files, no core code changes.

✅ **Database Schema:** Current schema already supports multiple routes:
- `sources` table has `country` and `visa_type` fields (supports any route)
- `route_subscriptions` table supports any origin/destination/visa combination
- No schema changes needed for route expansion

✅ **Multi-Route UI:** Admin UI architecture supports filtering and multi-route views:
- Route filtering already considered in API design
- Dashboard can aggregate across routes
- Change history can filter by route

**Required Additions:**
- New fetcher files in `fetchers/` directory (e.g., `uk_home_office_student.py`)
- Source configurations added to database (no code changes)
- UI enhancements for route filtering and comparison (frontend only)

**No Architecture Changes Required** - Epic 5 validates the plugin architecture design.

### Epic 6: Enhanced User Experience (v0.2) - Architecture Readiness

**Epic Summary:** Improve diff rendering, add alert forwarding, basic dashboard, and weekly summaries.

**Architecture Support:**

✅ **Diff Rendering:** Current diff generation uses `difflib` - can be enhanced with:
- HTML diff output (already supported by `difflib.HtmlDiff`)
- Side-by-side view (frontend rendering change only)
- Better formatting (CSS/styling, no backend changes)

✅ **Alert Forwarding:** Email alert system can be extended:
- Add `forward_to` field to `RouteSubscription` or create `alert_recipients` table
- Alert engine already supports multiple recipients per change
- Minimal database schema addition

✅ **Dashboard Enhancements:** Current dashboard architecture supports:
- Historical data queries (already in database)
- Aggregated statistics (SQL queries, no new components)
- Chart rendering (frontend library addition)

✅ **Weekly Summaries:** Email system can be extended:
- New scheduled job (GitHub Actions cron, weekly)
- Summary generation service (aggregates changes)
- Email template for summaries (Jinja2 template)

**Required Additions:**
- Database: Optional `alert_recipients` table for forwarding
- Service: Weekly summary generation service
- Frontend: Enhanced diff rendering components
- Scheduled Job: Weekly summary cron job

**Minimal Architecture Changes** - Mostly frontend and service layer enhancements.

### Epic 7: AI-Powered Intelligence (v1.0) - Architecture Readiness

**Epic Summary:** Add NLP summarization and impact assessment after 5+ paying customers establish trust.

**Architecture Support:**

✅ **Database Schema:** Already designed for AI enhancements:
- `policy_changes` table can add `ai_summary` TEXT field (nullable)
- `ai_summary_generated_at` timestamp field
- `impact_score` and `impact_assessment` fields can be added
- JSONB `metadata` field can store AI-related data

✅ **Service Architecture:** Service layer supports new services:
- New `AISummarizationService` component
- New `ImpactAssessmentService` component
- Integration with existing `AlertEngine` (adds summary to emails)

✅ **External API Integration:** Architecture already supports external APIs:
- Resend integration pattern can be replicated for LLM APIs
- `api/integrations/` directory structure ready
- Error handling and retry patterns established

**Required Additions:**

**New Components:**
- `AISummarizationService` - LLM API integration and prompt management
- `ImpactAssessmentService` - Impact scoring and assessment logic
- `AICostMonitor` - Track LLM API usage and costs

**Database Changes:**
```sql
-- Add AI-related fields to policy_changes
ALTER TABLE policy_changes 
ADD COLUMN ai_summary TEXT,
ADD COLUMN ai_summary_generated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN impact_score INTEGER,
ADD COLUMN impact_assessment TEXT;

-- Create AI usage tracking table
CREATE TABLE ai_usage_logs (
    id UUID PRIMARY KEY,
    policy_change_id UUID REFERENCES policy_changes(id),
    operation_type VARCHAR(50), -- 'summarization', 'impact_assessment'
    provider VARCHAR(50), -- 'openai', 'anthropic'
    tokens_used INTEGER,
    cost DECIMAL(10, 4),
    created_at TIMESTAMP WITH TIME ZONE
);
```

**External Services:**
- LLM API provider (OpenAI, Anthropic, etc.)
- API key management in environment variables
- Cost monitoring and alerting

**Architecture Impact:** Medium - New services and external API, but fits existing patterns.

### Epic 8: Platform & Integration Expansion (v1.0) - Architecture Readiness

**Epic Summary:** Add multi-route subscriptions, public API access, webhooks, and historical trend analysis.

**Architecture Support:**

✅ **Multi-Route Subscriptions:** Database schema can be extended:
- Option 1: Add `routes` JSONB array to `route_subscriptions` (simple)
- Option 2: Create `subscription_routes` junction table (normalized)
- Current single-route model can evolve without breaking changes

✅ **Public API:** Current REST API architecture supports extension:
- API versioning (`/api/v1/`) can be added
- Separate authentication for public API (API keys vs JWT)
- Rate limiting middleware can be added
- Current API structure is already RESTful and well-organized

✅ **Webhooks:** Architecture supports webhook infrastructure:
- New `WebhookDeliveryService` component
- Webhook subscription table (already noted in future schema evolution)
- Retry logic patterns already established (email alerts)
- Background job processing for webhook delivery

✅ **Analytics:** Database and query architecture supports:
- Historical data already stored (PolicyChanges with timestamps)
- Aggregation queries can be added (no schema changes)
- Caching layer can be added for expensive analytics queries

**Required Additions:**

**New Components:**
- `PublicAPIService` - Separate API layer for external consumers
- `WebhookDeliveryService` - Webhook delivery with retry logic
- `AnalyticsService` - Trend analysis and reporting
- `RateLimitingMiddleware` - API rate limiting

**Database Changes:**
```sql
-- Multi-route subscriptions (Option 1: JSONB array)
ALTER TABLE route_subscriptions 
ADD COLUMN routes JSONB DEFAULT '[]'::jsonb;

-- Or Option 2: Junction table
CREATE TABLE subscription_routes (
    subscription_id UUID REFERENCES route_subscriptions(id),
    origin_country VARCHAR(2),
    destination_country VARCHAR(2),
    visa_type VARCHAR(50),
    PRIMARY KEY (subscription_id, origin_country, destination_country, visa_type)
);

-- Webhook subscriptions
CREATE TABLE webhook_subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    url TEXT NOT NULL,
    secret_key VARCHAR(255),
    events TEXT[], -- ['policy_change', 'source_update']
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE
);

-- API keys for public API
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    rate_limit_per_hour INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Webhook delivery logs
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY,
    webhook_subscription_id UUID REFERENCES webhook_subscriptions(id),
    policy_change_id UUID REFERENCES policy_changes(id),
    status VARCHAR(20), -- 'pending', 'delivered', 'failed'
    response_code INTEGER,
    delivered_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT
);
```

**New External Services:**
- Webhook delivery infrastructure (can use existing background jobs)
- Analytics visualization library (frontend charting library)

**Architecture Impact:** Medium-High - New API layer, webhook infrastructure, but fits existing patterns.

### Architecture Evolution Strategy

**Principle:** MVP architecture is designed to support future epics without fundamental restructuring.

**Key Design Decisions That Support Future Epics:**

1. **Plugin Architecture (NFR12):** Enables Epic 5 (route expansion) without core changes
2. **Versioned Immutable Storage:** Supports Epic 8 (analytics) - all historical data preserved
3. **Repository Pattern:** Enables database schema evolution (Epic 7, 8) without breaking service layer
4. **Service Layer Separation:** New services (AI, Webhooks, Analytics) can be added without affecting existing code
5. **JSONB Metadata Fields:** Flexible storage for future features (AI data, webhook configs, etc.)
6. **RESTful API Design:** Can be extended with versioning and public API layer (Epic 8)
7. **Modular Component Design:** Components can be enhanced or replaced independently

**Migration Path for Each Epic:**

**Epic 5 (Route Expansion):**
- ✅ No architecture changes needed
- Add fetcher files, configure sources
- UI enhancements for multi-route support

**Epic 6 (Enhanced UX):**
- ✅ Minimal changes (frontend + optional database fields)
- Add weekly summary service
- Enhance diff rendering (frontend)

**Epic 7 (AI Intelligence):**
- Add AI service components
- Database: Add AI fields to `policy_changes`
- External: Integrate LLM API
- Cost: Monitor LLM API usage

**Epic 8 (Platform Expansion):**
- Add public API layer (separate routes, authentication)
- Add webhook infrastructure (service + database)
- Add analytics service (query layer)
- Database: Multi-route subscriptions, API keys, webhooks

**Risk Mitigation:**

- **Database Schema Evolution:** Alembic migrations handle all schema changes safely
- **API Versioning:** `/api/v1/` prefix allows breaking changes in future versions
- **Service Isolation:** New services don't affect existing functionality
- **External Dependencies:** LLM APIs and webhooks are optional features (graceful degradation)

**Cost Considerations:**

- **Epic 7 (AI):** LLM API costs must be monitored and budgeted
- **Epic 8 (Platform):** API traffic may require infrastructure scaling
- **Current Architecture:** Designed to keep MVP costs low (€50/month)
- **Future Scaling:** Railway can scale horizontally if needed

### Summary: Architecture Readiness for Future Epics

| Epic | Version | Architecture Readiness | Required Changes | Risk Level |
|------|---------|----------------------|------------------|------------|
| Epic 5: Route Expansion | v0.2 | ✅ Fully Ready | None (plugin architecture) | Low |
| Epic 6: Enhanced UX | v0.2 | ✅ Mostly Ready | Frontend + optional DB fields | Low |
| Epic 7: AI Intelligence | v1.0 | ✅ Well Supported | AI services + LLM API + DB fields | Medium |
| Epic 8: Platform Expansion | v1.0 | ✅ Well Supported | Public API + Webhooks + Analytics | Medium |

**Conclusion:** The MVP architecture is intentionally designed to support all planned future epics. The plugin architecture, service layer separation, flexible database schema, and modular component design enable future enhancements without requiring fundamental restructuring. This validates the architectural decisions made for the MVP.

---
