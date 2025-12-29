# Epic List

### Epic 1: Foundation & Core Infrastructure
Establish project setup, database schema, and basic API infrastructure while delivering a working health check endpoint and data persistence layer. Includes RouteSubscription API endpoints (CRUD) to enable route management before UI is built.

### Epic 2: Source Fetching & Change Detection Pipeline
Build the core monitoring capability: plugin-based source fetchers, normalization pipeline, and deterministic change detection with versioned policy storage.

### Epic 3: Alert System & Automation
Implement automated email alerts and scheduling system that proactively notifies users when policy changes are detected for their subscribed routes.

### Epic 4: Admin Interface
Create the admin web interface for managing route subscriptions, configuring sources, viewing change history, and manually triggering fetches for testing.

### Future Epics (Post-MVP Roadmap)

**Epic 5: Route Expansion (v0.2)** - Add 1-2 more routes and additional source fetchers after first paying customer validates the model.

**Epic 6: Enhanced User Experience (v0.2)** - Improve diff rendering, add alert forwarding, basic dashboard, and weekly summaries based on customer feedback.

**Epic 7: AI-Powered Intelligence (v1.0)** - Add NLP summarization and impact assessment after 5+ paying customers establish trust.

**Epic 8: Platform & Integration Expansion (v1.0)** - Add multi-route subscriptions, API access, webhooks, and historical trend analysis for platform capabilities.

*Note: Future epics are planned but not yet detailed with stories. See "Future Epics" section below for expanded goals and prerequisites.*

---
