# Route Configuration Guide

This guide explains how to add new immigration routes to the Policy Aggregator system. Adding a new route involves research, fetcher implementation, source configuration, and testing.

## Overview

The process of adding a new route consists of four main steps:

1. **Source Research** - Identify and document official government sources
2. **Fetcher Implementation** - Create fetchers for the identified sources
3. **Source Configuration** - Add sources to the database
4. **Testing** - Verify end-to-end pipeline works correctly

## Step 1: Source Research

Before implementing fetchers, research and document official government sources for the new route.

### Research Process

1. **Identify Route**: Determine origin country, destination country, and visa types
   - Example: India → UK, Student and Work visas

2. **Research Official Sources**:
   - Official government immigration websites
   - PDF policy documents and circulars
   - Embassy/consulate sources
   - Ministry of immigration sources

3. **Document Each Source**:
   - URL and access method
   - Content structure (HTML, PDF, API)
   - Update frequency (if known)
   - Scraping feasibility assessment
   - Legal/compliance review (robots.txt, terms of service)

4. **Prioritize Sources**: Identify 3-5 highest-priority sources per route based on:
   - Reliability and official status
   - Update frequency
   - Scraping feasibility
   - Content completeness

5. **Create Source Inventory**: Document all findings in `docs/sources/source-inventory-{route}.md`

### Example: Source Inventory Structure

```markdown
# Source Inventory: India → UK Route

## Route Information
- Origin Country: India (IN)
- Destination Country: United Kingdom (UK)
- Visa Types: Student, Work

## Source List

### 1. UK Home Office - Student Visa Information Page
- URL: https://www.gov.uk/student-visa
- Content Structure: HTML
- Scraping Feasibility: Easy
- Priority: High (1/5)
...
```

**Reference**: See `docs/sources/source-inventory-india-uk.md` and `docs/sources/source-inventory-india-canada.md` for complete examples.

## Step 2: Fetcher Implementation

Create fetchers for the high-priority sources identified in Step 1.

### Fetcher Naming Convention

Fetchers follow this naming pattern:
```
{country}_{agency}_{visa_type}.py
```

**Examples:**
- `uk_home_office_student.py` - UK Home Office Student visa
- `ca_ircc_work.py` - Canada IRCC Work visa

### Fetcher Implementation

1. **Create Fetcher File**: Create a new file in `fetchers/` directory

2. **Implement `fetch()` Function**:
   ```python
   from fetchers.base import FetchResult
   from fetchers.html_fetcher import fetch_html
   
   def fetch(url: str, metadata: Dict[str, Any]) -> FetchResult:
       """Fetch content from source."""
       result = fetch_html(url, metadata)
       
       if result.success:
           result.metadata['source'] = 'UK Home Office'
           result.metadata['route'] = 'India → UK'
       
       return result
   ```

3. **Add Source-Specific Metadata**: Include route, agency, and other relevant information

4. **Create Unit Tests**: Test successful fetch, error handling, and metadata extraction

5. **Create Integration Tests**: Test with real URLs (handle gracefully if unavailable)

**Reference**: See `fetchers/uk_home_office_student.py` and `fetchers/ca_ircc_student.py` for examples.

**Documentation**: See `docs/fetchers/README.md` for complete fetcher implementation guide.

## Step 3: Source Configuration

Add source configurations to the database for the new routes.

### Using the Script (Recommended)

Use the provided script to bulk-add sources:

```bash
python scripts/add_new_route_sources.py
```

The script:
- Checks for existing sources (skips duplicates)
- Creates sources with proper configuration
- Reports summary of added/skipped sources

### Manual Source Creation

Alternatively, create sources via API or directly in database:

**Via API:**
```bash
POST /api/sources
{
  "country": "UK",
  "visa_type": "Student",
  "url": "https://www.gov.uk/student-visa",
  "name": "UK Home Office Student Visa Information",
  "fetch_type": "html",
  "check_frequency": "daily",
  "is_active": true,
  "metadata": {
    "agency": "UK Home Office",
    "route": "India → UK"
  }
}
```

**Source Configuration Fields:**
- `country`: Destination country code (2 characters, e.g., "UK", "CA")
- `visa_type`: Visa type (e.g., "Student", "Work")
- `url`: Source URL to fetch from
- `name`: Human-readable source name
- `fetch_type`: "html" or "pdf"
- `check_frequency`: "daily", "weekly", or "custom"
- `is_active`: Whether source is currently monitored
- `metadata`: Additional configuration (JSON)

**Important**: 
- Country code must match destination country (not origin)
- Multiple sources can monitor the same route (redundancy)
- Sources are matched to routes by `destination_country` and `visa_type`

### Script Template

To create a script for your new route, copy `scripts/add_new_route_sources.py` and modify:

1. Update source list with your route's sources
2. Update country codes and URLs
3. Update metadata (agency, route, description)
4. Run script to add sources

**Reference**: See `scripts/add_new_route_sources.py` for complete example.

## Step 4: Testing

Verify the end-to-end pipeline works correctly for new routes.

### Route-to-Source Mapping

The route-to-source mapping is automatic and route-agnostic. It matches:
- `route.destination_country == source.country`
- `route.visa_type == source.visa_type`

**Verification:**
1. Create route subscription for new route
2. Verify sources are mapped correctly using RouteMapper
3. Test that routes are isolated (UK route doesn't match Canada sources)

### End-to-End Pipeline Test

Test the complete flow:
1. Create route subscription for new route
2. Manually trigger fetch for route sources
3. Verify fetch → normalization → change detection pipeline works
4. If change detected, verify PolicyChange record created
5. Verify PolicyVersion records created correctly

### Alert Testing

Verify alerts work for new routes:
1. Create route subscription with test email
2. Trigger fetch that detects a change
3. Verify alert engine sends email
4. Verify email content includes correct route information
5. Verify EmailAlert record created

### Integration Tests

Create integration tests in `tests/integration/test_routes/test_new_route_expansion.py`:

```python
async def test_new_route_source_mapping(self, db_session):
    """Test: create route subscription and verify sources are mapped."""
    # Create sources
    # Create route subscription
    # Verify mapping
```

**Reference**: See `tests/integration/test_routes/test_new_route_expansion.py` for complete examples.

## Route-to-Source Mapping Logic

The system automatically maps route subscriptions to sources based on:

1. **Destination Country Match**: `route.destination_country == source.country`
2. **Visa Type Match**: `route.visa_type == source.visa_type`
3. **Active Status**: Only active sources and routes are matched

**Key Points:**
- Origin country is NOT used in matching (sources are destination-specific)
- Many-to-many relationship (one source can serve multiple routes)
- Mapping is route-agnostic (works for any country/visa combination)
- No code changes needed for new routes

**Example:**
- Route: `origin=IN, destination=UK, visa_type=Student`
- Matches Source: `country=UK, visa_type=Student`
- Does NOT match: `country=CA, visa_type=Student` (wrong destination)
- Does NOT match: `country=UK, visa_type=Work` (wrong visa type)

## Database Schema

The database schema already supports multiple routes. No migrations needed.

**Source Table:**
- `country`: VARCHAR(2) - ISO country code (supports any country)
- `visa_type`: VARCHAR(50) - Visa type (supports any visa type)
- Index on `(country, visa_type)` for efficient queries

**RouteSubscription Table:**
- `origin_country`: VARCHAR(2) - Origin country code
- `destination_country`: VARCHAR(2) - Destination country code
- `visa_type`: VARCHAR(50) - Visa type
- Index on `(destination_country, visa_type)` for efficient queries

## Examples

### Example 1: India → UK Route

**Sources Added:**
1. UK Home Office Student Visa (https://www.gov.uk/student-visa)
2. UK Home Office Skilled Worker Visa (https://www.gov.uk/skilled-worker-visa)
3. UK Immigration Rules (https://www.gov.uk/guidance/immigration-rules)

**Fetchers Created:**
- `fetchers/uk_home_office_student.py`
- `fetchers/uk_home_office_work.py`
- `fetchers/uk_home_office_immigration_rules.py`

**Route Subscriptions:**
- `origin=IN, destination=UK, visa_type=Student`
- `origin=IN, destination=UK, visa_type=Work`

### Example 2: India → Canada Route

**Sources Added:**
1. IRCC Study Permit (https://www.canada.ca/.../study-permit.html)
2. IRCC Work in Canada (https://www.canada.ca/.../work-canada.html)
3. IRCC Operational Bulletins (https://www.canada.ca/.../operational-bulletins-manuals.html)

**Fetchers Created:**
- `fetchers/ca_ircc_student.py`
- `fetchers/ca_ircc_work.py`
- `fetchers/ca_ircc_operational_bulletins.py`

**Route Subscriptions:**
- `origin=IN, destination=CA, visa_type=Student`
- `origin=IN, destination=CA, visa_type=Work`

## Troubleshooting

### Sources Not Matching Routes

**Problem**: Route subscription created but no sources found

**Solutions:**
- Verify source `country` matches route `destination_country` (case-sensitive)
- Verify source `visa_type` matches route `visa_type` (exact match)
- Verify source `is_active` is `True`
- Check RouteMapper logs for warnings

### Fetcher Not Found

**Problem**: Fetcher not discovered by FetcherManager

**Solutions:**
- Verify fetcher file follows naming convention: `{country}_{agency}_{visa_type}.py`
- Verify `fetch()` function exists in module
- Check for import errors in logs
- Verify fetcher is in `fetchers/` directory

### Fetch Failures

**Problem**: Source fetch returns `success=False`

**Solutions:**
- Check `error_message` in FetchResult for details
- Verify URL is accessible
- Check network connectivity
- Review source website for changes (HTML structure, authentication, etc.)
- Test with browser to see if source requires JavaScript or special headers

## Related Documentation

- [Fetcher Architecture](fetchers/README.md) - Fetcher implementation guide
- [Source Inventory Examples](sources/) - Source research documentation
- [Route-to-Source Mapping](stories/3.1.route-to-source-mapping-logic.story.md) - Mapping logic details
- [Database Schema](architecture/database-schema.md) - Database structure
- [Coding Standards](architecture/coding-standards.md) - Development standards

## Summary

Adding a new route involves:
1. ✅ Research and document sources (Story 5.1)
2. ✅ Implement fetchers (Story 5.2)
3. ✅ Configure sources in database (Story 5.3)
4. ✅ Test end-to-end pipeline (Story 5.3)

The system is designed to be route-agnostic, so most components work automatically for new routes without code changes. The main work is in research, fetcher implementation, and source configuration.

