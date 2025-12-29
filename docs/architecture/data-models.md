# Data Models

The core data models define the business entities that will be shared between frontend and backend. These models represent the immutable versioned policy storage system and route-scoped monitoring capabilities.

### Source

**Purpose:** Represents a government source that provides policy documents. Each source is associated with a specific country, visa type, and has configuration for how it should be fetched (HTML or PDF) and how frequently it should be checked.

**Key Attributes:**
- `id`: string (UUID) - Unique identifier for the source
- `country`: string - Country code (e.g., "DE" for Germany)
- `visaType`: string - Type of visa (e.g., "Student", "Work")
- `url`: string - Source URL to fetch from
- `fetchType`: "html" | "pdf" - How to fetch content (HTML scraping or PDF extraction)
- `checkFrequency`: "daily" | "weekly" | "custom" - How often to check this source
- `name`: string - Human-readable name for the source
- `lastCheckedAt`: Date | null - Timestamp of last successful fetch (FR6)
- `lastChangeDetectedAt`: Date | null - Timestamp of last change detected
- `isActive`: boolean - Whether source is currently being monitored
- `metadata`: Record<string, any> - Additional configuration (JSONB field for flexibility)
- `createdAt`: Date - When source was created
- `updatedAt`: Date - When source was last modified

**TypeScript Interface:**
```typescript
interface Source {
  id: string;
  country: string;
  visaType: string;
  url: string;
  fetchType: "html" | "pdf";
  checkFrequency: "daily" | "weekly" | "custom";
  name: string;
  lastCheckedAt: Date | null;
  lastChangeDetectedAt: Date | null;
  isActive: boolean;
  metadata: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}
```

**Relationships:**
- One Source has many PolicyVersions (one-to-many)
- One Source has many PolicyChanges (one-to-many)
- Many Sources can be associated with one RouteSubscription (many-to-many, via route matching)

**Design Decisions:**
- `metadata` as JSONB allows storing source-specific configuration without schema changes
- `lastCheckedAt` and `lastChangeDetectedAt` are nullable to handle sources that haven't been checked yet
- `isActive` flag allows disabling sources without deleting them (preserves history)

### PolicyVersion

**Purpose:** Stores an immutable version of policy content fetched from a source. Each fetch creates a new PolicyVersion record, never overwriting previous versions. This enables complete audit trail and change detection through hash comparison.

**Key Attributes:**
- `id`: string (UUID) - Unique identifier for this version
- `sourceId`: string (UUID) - Foreign key to Source
- `contentHash`: string - SHA256 hash of normalized content (FR7, NFR6)
- `rawText`: string - Full text content after normalization (FR15)
- `fetchedAt`: Date - Timestamp when content was fetched (FR7)
- `normalizedAt`: Date - Timestamp when normalization was applied
- `contentLength`: number - Character count of raw text
- `fetchDuration`: number - Time taken to fetch in milliseconds
- `createdAt`: Date - When this version was created

**TypeScript Interface:**
```typescript
interface PolicyVersion {
  id: string;
  sourceId: string;
  contentHash: string; // SHA256, 64 characters
  rawText: string;
  fetchedAt: Date;
  normalizedAt: Date;
  contentLength: number;
  fetchDuration: number;
  createdAt: Date;
}
```

**Relationships:**
- Many PolicyVersions belong to one Source (many-to-one)
- One PolicyVersion can be referenced as `oldHash` in PolicyChange
- One PolicyVersion can be referenced as `newHash` in PolicyChange

**Design Decisions:**
- Immutable records: PolicyVersions are never updated, only new versions created (NFR4)
- `contentHash` is the primary mechanism for change detection (FR8, NFR6)
- `rawText` stored in database (no file storage needed for MVP)
- `normalizedAt` separate from `fetchedAt` to track normalization timing
- `fetchDuration` helps monitor source performance

### PolicyChange

**Purpose:** Records when a change is detected between two PolicyVersions of the same source. Stores the diff text and timestamps to provide complete audit trail and enable email alerts with change details.

**Key Attributes:**
- `id`: string (UUID) - Unique identifier for this change
- `sourceId`: string (UUID) - Foreign key to Source
- `oldHash`: string - SHA256 hash of previous version (FR10)
- `newHash`: string - SHA256 hash of new version (FR10)
- `diff`: string - Text diff showing what changed (FR9, FR10)
- `detectedAt`: Date - Timestamp when change was detected (FR10)
- `oldVersionId`: string (UUID) - Foreign key to previous PolicyVersion
- `newVersionId`: string (UUID) - Foreign key to new PolicyVersion
- `diffLength`: number - Character count of diff text
- `alertSentAt`: Date | null - Timestamp when email alert was sent
- `createdAt`: Date - When this change record was created

**TypeScript Interface:**
```typescript
interface PolicyChange {
  id: string;
  sourceId: string;
  oldHash: string;
  newHash: string;
  diff: string;
  detectedAt: Date;
  oldVersionId: string;
  newVersionId: string;
  diffLength: number;
  alertSentAt: Date | null;
  createdAt: Date;
}
```

**Relationships:**
- Many PolicyChanges belong to one Source (many-to-one)
- One PolicyChange references one old PolicyVersion (many-to-one)
- One PolicyChange references one new PolicyVersion (many-to-one)
- Many PolicyChanges can trigger alerts for RouteSubscriptions (many-to-many, via route matching)

**Design Decisions:**
- Stores both hash strings and version IDs for flexibility and performance
- `diff` stored as text (raw unified diff format acceptable for MVP per PRD)
- `alertSentAt` tracks email delivery for auditability (NFR8)
- `diffLength` helps identify significant vs minor changes

### RouteSubscription

**Purpose:** Represents a user's subscription to monitor a specific route (origin country → destination country, visa type). When changes are detected for sources matching this route, email alerts are sent to the subscribed email address.

**Key Attributes:**
- `id`: string (UUID) - Unique identifier for subscription
- `originCountry`: string - Origin country code (e.g., "IN" for India) (FR1)
- `destinationCountry`: string - Destination country code (e.g., "DE" for Germany) (FR1)
- `visaType`: string - Type of visa (e.g., "Student", "Work") (FR1)
- `email`: string - Email address to send alerts to (FR11, NFR9)
- `isActive`: boolean - Whether subscription is active
- `createdAt`: Date - When subscription was created
- `updatedAt`: Date - When subscription was last modified

**TypeScript Interface:**
```typescript
interface RouteSubscription {
  id: string;
  originCountry: string;
  destinationCountry: string;
  visaType: string;
  email: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}
```

**Relationships:**
- Many RouteSubscriptions can match one Source (many-to-many, via country/visa matching)
- One RouteSubscription can receive alerts for many PolicyChanges (many-to-many, via route matching)

**Design Decisions:**
- Simple structure: route is defined by three fields (origin, destination, visa type)
- No `orgId` in MVP (single admin user per PRD FR2)
- `email` is the only user data collected (NFR9)
- `isActive` allows disabling subscriptions without deletion

### EmailAlert

**Purpose:** Tracks email alerts that have been sent for policy changes. Provides audit trail for email delivery and enables monitoring of alert system reliability (NFR2, NFR8).

**Key Attributes:**
- `id`: string (UUID) - Unique identifier for alert
- `policyChangeId`: string (UUID) - Foreign key to PolicyChange
- `routeSubscriptionId`: string (UUID) - Foreign key to RouteSubscription
- `sentAt`: Date - Timestamp when email was sent
- `emailProvider`: string - Email service used (e.g., "resend")
- `emailProviderId`: string | null - Provider's message ID for tracking
- `status`: "sent" | "failed" | "bounced" - Delivery status
- `errorMessage`: string | null - Error details if sending failed
- `createdAt`: Date - When alert record was created

**TypeScript Interface:**
```typescript
interface EmailAlert {
  id: string;
  policyChangeId: string;
  routeSubscriptionId: string;
  sentAt: Date;
  emailProvider: string;
  emailProviderId: string | null;
  status: "sent" | "failed" | "bounced";
  errorMessage: string | null;
  createdAt: Date;
}
```

**Relationships:**
- Many EmailAlerts belong to one PolicyChange (many-to-one)
- Many EmailAlerts belong to one RouteSubscription (many-to-one)

**Design Decisions:**
- Separate table for auditability and monitoring (NFR8)
- `emailProviderId` enables tracking delivery status via provider API
- `status` field supports retry logic for failed sends
- `errorMessage` helps diagnose email delivery issues

### Data Model Relationships Summary

```
Source (1) ──< (many) PolicyVersion
Source (1) ──< (many) PolicyChange
PolicyVersion (1) ──< (many) PolicyChange (as oldVersion)
PolicyVersion (1) ──< (many) PolicyChange (as newVersion)
PolicyChange (1) ──< (many) EmailAlert
RouteSubscription (1) ──< (many) EmailAlert
Source (many) ── (many) RouteSubscription (via country/visa matching)
```

**Key Relationship Notes:**
- Sources are matched to RouteSubscriptions by country and visaType (not stored as explicit foreign keys)
- PolicyChanges trigger EmailAlerts for matching RouteSubscriptions based on route criteria
- All relationships support querying and filtering for the admin interface requirements

**Data Sharing and Deduplication:**
- **Sources are SHARED:** The unique constraint on `(url, country, visa_type)` ensures that if 10 users subscribe to the same route (e.g., India → Germany, Student visa), and that route uses the same source URL, only ONE source record exists in the database. The same source is reused for all matching route subscriptions.
- **PolicyVersions are SHARED:** PolicyVersions are linked to Sources (via `source_id`), not to RouteSubscriptions. This means if 10 users monitor the same source, only ONE set of policy versions is stored. When the source is fetched, a new PolicyVersion is created once, and all 10 users benefit from that single fetch.
- **PolicyChanges are SHARED:** PolicyChanges are also linked to Sources, not RouteSubscriptions. When a change is detected for a source, only ONE PolicyChange record is created, regardless of how many route subscriptions are monitoring that source.
- **RouteSubscriptions are PER-USER:** Each user's subscription is stored separately (with their email address). Multiple users can subscribe to the same route, but each subscription is a separate record.
- **EmailAlerts are PER-USER:** EmailAlerts link PolicyChanges to RouteSubscriptions. When a change is detected, one EmailAlert record is created for each matching RouteSubscription. So if 10 users are monitoring the same source and a change is detected, 10 EmailAlert records are created (one per user), but only ONE PolicyChange record exists.

**Example Scenario:**
If 10 users subscribe to route "India → Germany, Student visa", and that route uses source "https://example.com/student-visa-policy":
- **1 Source record** (shared by all 10 users)
- **10 RouteSubscription records** (one per user with their email)
- **N PolicyVersion records** (one per fetch, shared by all 10 users)
- **M PolicyChange records** (one per detected change, shared by all 10 users)
- **M × 10 EmailAlert records** (one per change per user = 10 alerts per change)

This design ensures efficient storage and fetching: the source is fetched once per day, not 10 times, and policy versions/changes are stored once, not duplicated per user.

---

