# Source Inventory - India → Germany Route

This document provides a comprehensive inventory of all policy sources for monitoring India → Germany immigration routes.

## Overview

**Total Sources:** 8  
**Student Visa Sources:** 3  
**Work Visa Sources:** 5  
**HTML Sources:** 8  
**PDF Sources:** 0  
**Route:** India → Germany

## Source Inventory

### Student Visa Sources (3)

#### 1. Germany BMI Student Visa Information
- **Fetcher:** `fetchers/de_bmi_student.py`
- **Agency:** Bundesministerium des Innern (BMI) - Federal Ministry of the Interior
- **URL:** https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/student-visa.html
- **Access Method:** HTML scraping
- **Content Structure:** HTML page with FAQ format
- **Technical Details:**
  - Uses standard HTML fetcher utilities
  - Extracts text from main content area
  - Handles standard government website structure

#### 2. Germany Auswärtiges Amt Student Visa Information
- **Fetcher:** `fetchers/de_auswaertiges_amt_student.py`
- **Agency:** Auswärtiges Amt - Federal Foreign Office
- **URL:** https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-students
- **Access Method:** HTML scraping
- **Content Structure:** HTML page with visa information
- **Technical Details:**
  - Uses standard HTML fetcher utilities
  - Extracts text from main content area
  - Handles standard government website structure

#### 3. Germany DAAD Student Visa Information
- **Fetcher:** `fetchers/de_daad_student.py`
- **Agency:** Deutscher Akademischer Austauschdienst (DAAD) - German Academic Exchange Service
- **URL:** https://www.daad.de/en/study-and-research-in-germany/plan-your-studies/entry-and-residence/
- **Access Method:** HTML scraping
- **Content Structure:** HTML page with student-specific immigration information
- **Technical Details:**
  - Uses standard HTML fetcher utilities
  - Extracts text from main content area
  - Handles standard government-affiliated website structure

### Work Visa Sources (5)

#### 1. Germany BMI Skilled Worker Visa Information
- **Fetcher:** `fetchers/de_bmi_work.py`
- **Agency:** Bundesministerium des Innern (BMI) - Federal Ministry of the Interior
- **URL:** https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/skilled-workers.html
- **Access Method:** HTML scraping
- **Content Structure:** HTML page with FAQ format
- **Technical Details:**
  - Uses standard HTML fetcher utilities
  - Extracts text from main content area
  - Handles standard government website structure

#### 2. Germany Auswärtiges Amt Work Visa Information
- **Fetcher:** `fetchers/de_auswaertiges_amt_work.py`
- **Agency:** Auswärtiges Amt - Federal Foreign Office
- **URL:** https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-employment
- **Access Method:** HTML scraping
- **Content Structure:** HTML page with visa information
- **Technical Details:**
  - Uses standard HTML fetcher utilities
  - Extracts text from main content area
  - Handles standard government website structure

#### 3. Make it in Germany Skilled Worker Visa Information
- **Fetcher:** `fetchers/de_make_it_in_germany_work.py`
- **Agency:** Make it in Germany (Official Government Portal)
- **URL:** https://www.make-it-in-germany.com/en/visa/skilled-workers
- **Access Method:** HTML scraping
- **Content Structure:** HTML page with skilled worker information
- **Technical Details:**
  - Uses standard HTML fetcher utilities
  - Extracts text from main content area
  - Handles standard government portal structure

#### 4. Germany BAMF Work Visa Information
- **Fetcher:** `fetchers/de_bamf_work.py`
- **Agency:** Bundesamt für Migration und Flüchtlinge (BAMF) - Federal Office for Migration and Refugees
- **URL:** https://www.bamf.de/EN/Themen/MigrationAufenthalt/ZuwandererDrittstaaten/Migrathek/migrathek-node.html
- **Access Method:** HTML scraping
- **Content Structure:** HTML page with immigration procedures and residence permit information
- **Technical Details:**
  - Uses standard HTML fetcher utilities
  - Extracts text from main content area
  - Handles standard government website structure
  - May require cookie consent handling

#### 5. Germany Bundesagentur für Arbeit Work Visa Information
- **Fetcher:** `fetchers/de_arbeitsagentur_work.py`
- **Agency:** Bundesagentur für Arbeit (BA) - Federal Employment Agency
- **URL:** https://www.arbeitsagentur.de/en/working-in-germany
- **Access Method:** HTML scraping
- **Content Structure:** HTML page with work permit and employment information
- **Technical Details:**
  - Uses standard HTML fetcher utilities
  - Extracts text from main content area
  - Handles standard government website structure

## Source Coverage

### By Agency
- **BMI (Bundesministerium des Innern):** 2 sources (Student, Work)
- **Auswärtiges Amt (Federal Foreign Office):** 2 sources (Student, Work)
- **Make it in Germany:** 1 source (Work)
- **BAMF (Federal Office for Migration and Refugees):** 1 source (Work)
- **DAAD (German Academic Exchange Service):** 1 source (Student)
- **Bundesagentur für Arbeit (Federal Employment Agency):** 1 source (Work)

### By Visa Type
- **Student:** 3 sources
  - BMI
  - Auswärtiges Amt
  - DAAD
- **Work:** 5 sources
  - BMI
  - Auswärtiges Amt
  - Make it in Germany
  - BAMF
  - Bundesagentur für Arbeit

## Technical Implementation

### Fetcher Architecture
All fetchers follow the plugin architecture:
- Located in `fetchers/` directory
- Naming convention: `{country}_{agency}_{visa_type}.py`
- Implement standard `fetch(url: str, metadata: Dict[str, Any]) -> FetchResult` function
- Use standard HTML fetcher utilities from `fetchers/html_fetcher.py`

### Database Configuration
All sources are configured in the database via `scripts/add_germany_sources.py`:
- Country: "DE"
- Check Frequency: "daily"
- Fetch Type: "html"
- Is Active: True

### Fetcher Manager
The Fetcher Manager automatically discovers and loads all fetchers:
- Scans `fetchers/` directory
- Matches sources to fetchers by country and visa type
- No core code changes needed to add new fetchers

## Monitoring Status

All sources are configured for daily monitoring. The daily job will:
1. Load all active sources for India → Germany route
2. Match each source to appropriate fetcher
3. Execute fetch operation
4. Store policy versions
5. Detect changes
6. Send alerts if changes detected

## Notes

- All sources are official German government or government-affiliated websites
- URLs may need periodic verification to ensure they remain valid
- Some sources may require cookie consent handling (e.g., BAMF)
- All fetchers use standard error handling and retry logic
- Content extraction uses semantic HTML elements (main, article, etc.)

## Adding New Sources

To add a new source:
1. Research and verify source is official and publicly accessible
2. Create fetcher file: `fetchers/de_{agency}_{visa_type}.py`
3. Implement `fetch()` function using `fetch_html()` utilities
4. Add source configuration to `scripts/add_germany_sources.py`
5. Run script to add source to database
6. Update this inventory document
7. Update `docs/sources.md` documentation

## Testing

Unit tests: `tests/unit/test_fetchers/test_de_*.py`  
Integration tests: `tests/integration/test_fetchers/test_germany_sources.py`  
All sources test: `tests/integration/test_fetchers/test_all_germany_sources.py`

