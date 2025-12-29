# API Specification

The API follows RESTful principles with JSON request/response bodies. FastAPI automatically generates OpenAPI 3.0 documentation accessible at `/docs`. All endpoints except `/health` and `/auth/login` require authentication.

### REST API Specification

```yaml
openapi: 3.0.0
info:
  title: Policy Aggregator API
  version: 1.0.0
  description: REST API for managing route subscriptions, sources, and viewing policy changes
servers:
  - url: https://api.policyaggregator.com
    description: Production server
  - url: http://localhost:8000
    description: Local development server

paths:
  # Health Check
  /health:
    get:
      summary: Health check endpoint
      description: Returns application and database health status
      tags: [System]
      responses:
        '200':
          description: Application is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  database:
                    type: string
                    example: "connected"
                  timestamp:
                    type: string
                    format: date-time

  # Authentication
  /auth/login:
    post:
      summary: Admin login
      description: Authenticate admin user and receive session token
      tags: [Authentication]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [username, password]
              properties:
                username:
                  type: string
                  example: "admin"
                password:
                  type: string
                  format: password
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  token_type:
                    type: string
                    example: "bearer"
        '401':
          description: Invalid credentials

  /auth/logout:
    post:
      summary: Admin logout
      description: Invalidate current session
      tags: [Authentication]
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Logout successful

  # Route Subscriptions
  /api/routes:
    get:
      summary: List route subscriptions
      description: Get all route subscriptions with optional pagination
      tags: [Routes]
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: List of route subscriptions
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/RouteSubscription'
                  total:
                    type: integer
                  page:
                    type: integer
                  page_size:
                    type: integer

    post:
      summary: Create route subscription
      description: Create a new route subscription
      tags: [Routes]
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [originCountry, destinationCountry, visaType, email]
              properties:
                originCountry:
                  type: string
                  example: "IN"
                destinationCountry:
                  type: string
                  example: "DE"
                visaType:
                  type: string
                  example: "Student"
                email:
                  type: string
                  format: email
      responses:
        '201':
          description: Route subscription created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RouteSubscription'
        '400':
          description: Validation error
        '409':
          description: Route subscription already exists

  /api/routes/{id}:
    get:
      summary: Get route subscription
      description: Get specific route subscription by ID
      tags: [Routes]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Route subscription details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RouteSubscription'
        '404':
          description: Route subscription not found

    delete:
      summary: Delete route subscription
      description: Delete a route subscription
      tags: [Routes]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: Route subscription deleted
        '404':
          description: Route subscription not found

  # Sources
  /api/sources:
    get:
      summary: List sources
      description: Get all sources with optional filtering and pagination
      tags: [Sources]
      security:
        - bearerAuth: []
      parameters:
        - name: country
          in: query
          schema:
            type: string
        - name: visaType
          in: query
          schema:
            type: string
        - name: isActive
          in: query
          schema:
            type: boolean
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: List of sources
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/Source'
                  total:
                    type: integer

    post:
      summary: Create source
      description: Create a new policy source
      tags: [Sources]
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [country, visaType, url, fetchType, checkFrequency, name]
              properties:
                country:
                  type: string
                  example: "DE"
                visaType:
                  type: string
                  example: "Student"
                url:
                  type: string
                  format: uri
                fetchType:
                  type: string
                  enum: [html, pdf]
                checkFrequency:
                  type: string
                  enum: [daily, weekly, custom]
                name:
                  type: string
                metadata:
                  type: object
      responses:
        '201':
          description: Source created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Source'
        '400':
          description: Validation error

  /api/sources/{id}:
    get:
      summary: Get source
      description: Get specific source with status information
      tags: [Sources]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Source details
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/Source'
                  - type: object
                    properties:
                      lastCheckedAt:
                        type: string
                        format: date-time
                        nullable: true
                      lastChangeDetectedAt:
                        type: string
                        format: date-time
                        nullable: true
        '404':
          description: Source not found

    put:
      summary: Update source
      description: Update source configuration
      tags: [Sources]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                url:
                  type: string
                  format: uri
                fetchType:
                  type: string
                  enum: [html, pdf]
                checkFrequency:
                  type: string
                  enum: [daily, weekly, custom]
                name:
                  type: string
                isActive:
                  type: boolean
                metadata:
                  type: object
      responses:
        '200':
          description: Source updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Source'
        '404':
          description: Source not found

    delete:
      summary: Delete source
      description: Delete a source (cascades to related records)
      tags: [Sources]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: Source deleted
        '404':
          description: Source not found

  # Policy Changes
  /api/changes:
    get:
      summary: List policy changes
      description: Get policy changes with filtering by route, source, and date range
      tags: [Changes]
      security:
        - bearerAuth: []
      parameters:
        - name: routeId
          in: query
          schema:
            type: string
            format: uuid
        - name: sourceId
          in: query
          schema:
            type: string
            format: uuid
        - name: originCountry
          in: query
          schema:
            type: string
        - name: destinationCountry
          in: query
          schema:
            type: string
        - name: visaType
          in: query
          schema:
            type: string
        - name: startDate
          in: query
          schema:
            type: string
            format: date
        - name: endDate
          in: query
          schema:
            type: string
            format: date
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: List of policy changes
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/PolicyChange'
                  total:
                    type: integer

  /api/changes/{id}:
    get:
      summary: Get policy change
      description: Get specific policy change with full diff
      tags: [Changes]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Policy change details
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/PolicyChange'
                  - type: object
                    properties:
                      source:
                        $ref: '#/components/schemas/Source'
                      oldVersion:
                        $ref: '#/components/schemas/PolicyVersion'
                      newVersion:
                        $ref: '#/components/schemas/PolicyVersion'
        '404':
          description: Policy change not found

  # Dashboard/Stats
  /api/dashboard:
    get:
      summary: Get dashboard statistics
      description: Get overview statistics for dashboard
      tags: [Dashboard]
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Dashboard statistics
          content:
            application/json:
              schema:
                type: object
                properties:
                  totalRoutes:
                    type: integer
                  totalSources:
                    type: integer
                  activeSources:
                    type: integer
                  changesLast7Days:
                    type: integer
                  changesLast30Days:
                    type: integer
                  recentChanges:
                    type: array
                    items:
                      $ref: '#/components/schemas/PolicyChange'
                  sourceHealth:
                    type: array
                    items:
                      type: object
                      properties:
                        sourceId:
                          type: string
                          format: uuid
                        sourceName:
                          type: string
                        lastCheckedAt:
                          type: string
                          format: date-time
                          nullable: true
                        status:
                          type: string
                          enum: [healthy, stale, error]

  # Manual Trigger/Testing
  /api/sources/{id}/trigger:
    post:
      summary: Manually trigger source fetch
      description: Manually trigger a fetch for a specific source (testing/debugging)
      tags: [Sources]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Fetch completed
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  sourceId:
                    type: string
                    format: uuid
                  fetchedAt:
                    type: string
                    format: date-time
                  contentHash:
                    type: string
                  contentLength:
                    type: integer
                  changeDetected:
                    type: boolean
                  policyChangeId:
                    type: string
                    format: uuid
                    nullable: true
                  error:
                    type: string
                    nullable: true
        '404':
          description: Source not found
        '500':
          description: Fetch failed

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    RouteSubscription:
      type: object
      properties:
        id:
          type: string
          format: uuid
        originCountry:
          type: string
        destinationCountry:
          type: string
        visaType:
          type: string
        email:
          type: string
          format: email
        isActive:
          type: boolean
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

    Source:
      type: object
      properties:
        id:
          type: string
          format: uuid
        country:
          type: string
        visaType:
          type: string
        url:
          type: string
          format: uri
        fetchType:
          type: string
          enum: [html, pdf]
        checkFrequency:
          type: string
          enum: [daily, weekly, custom]
        name:
          type: string
        isActive:
          type: boolean
        metadata:
          type: object
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

    PolicyVersion:
      type: object
      properties:
        id:
          type: string
          format: uuid
        sourceId:
          type: string
          format: uuid
        contentHash:
          type: string
        fetchedAt:
          type: string
          format: date-time
        contentLength:
          type: integer
        createdAt:
          type: string
          format: date-time

    PolicyChange:
      type: object
      properties:
        id:
          type: string
          format: uuid
        sourceId:
          type: string
          format: uuid
        oldHash:
          type: string
        newHash:
          type: string
        diff:
          type: string
        detectedAt:
          type: string
          format: date-time
        diffLength:
          type: integer
        alertSentAt:
          type: string
          format: date-time
          nullable: true
        createdAt:
          type: string
          format: date-time
```

### Authentication

All endpoints except `/health` and `/auth/login` require Bearer token authentication. The login endpoint returns a JWT token that should be included in the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens expire after 24 hours. The logout endpoint invalidates the current token.

### Error Response Format

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email"
    },
    "timestamp": "2025-01-27T10:00:00Z",
    "requestId": "req_abc123"
  }
}
```

Common error codes:
- `VALIDATION_ERROR` - Request validation failed (400)
- `UNAUTHORIZED` - Authentication required (401)
- `FORBIDDEN` - Insufficient permissions (403)
- `NOT_FOUND` - Resource not found (404)
- `CONFLICT` - Resource conflict (e.g., duplicate route) (409)
- `INTERNAL_ERROR` - Server error (500)

### Pagination

List endpoints support pagination via `page` and `page_size` query parameters. Response includes:
- `items` - Array of results
- `total` - Total number of items
- `page` - Current page number
- `page_size` - Items per page

### Filtering and Sorting

- **Routes:** No filtering (simple list)
- **Sources:** Filter by `country`, `visaType`, `isActive`
- **Changes:** Filter by `routeId`, `sourceId`, `originCountry`, `destinationCountry`, `visaType`, `startDate`, `endDate`

Sorting is not implemented in MVP (defaults to creation date descending).

---
