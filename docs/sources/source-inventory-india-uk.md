# Source Inventory: India → UK Route

## Route Information

- **Origin Country:** India (IN)
- **Destination Country:** United Kingdom (UK/GB)
- **Visa Types:** Student, Work (Skilled Worker)
- **Research Date:** 2025-01-27
- **Status:** Research Complete - Ready for Implementation

## Source List

### 1. UK Home Office - Student Visa Information Page

- **Source Name:** UK Home Office Student Visa Information
- **Agency:** UK Home Office / UK Visas and Immigration (UKVI)
- **URL:** https://www.gov.uk/student-visa
- **Visa Type:** Student
- **Content Structure:** HTML
- **Access Method:** Direct URL, publicly accessible
- **Update Frequency:** Regular updates when policy changes occur (typically monthly/quarterly)
- **Scraping Feasibility:** Easy - Standard HTML page, well-structured content
- **Special Requirements:** None - No authentication required
- **Language:** English
- **Official Status:** ✅ Official UK Government source
- **Legal/Compliance:** 
  - Publicly accessible: Yes
  - robots.txt: Allows crawling (standard GOV.UK policy)
  - Terms of Service: Standard UK government website terms, allows automated access for public information
- **Priority:** High (1/5)
- **Rationale:** Primary official source for student visa information, regularly updated, easy to scrape

### 2. UK Home Office - Skilled Worker Visa Information Page

- **Source Name:** UK Home Office Skilled Worker Visa Information
- **Agency:** UK Home Office / UK Visas and Immigration (UKVI)
- **URL:** https://www.gov.uk/skilled-worker-visa
- **Visa Type:** Work
- **Content Structure:** HTML
- **Access Method:** Direct URL, publicly accessible
- **Update Frequency:** Regular updates when policy changes occur (typically monthly/quarterly)
- **Scraping Feasibility:** Easy - Standard HTML page, well-structured content
- **Special Requirements:** None - No authentication required
- **Language:** English
- **Official Status:** ✅ Official UK Government source
- **Legal/Compliance:** 
  - Publicly accessible: Yes
  - robots.txt: Allows crawling (standard GOV.UK policy)
  - Terms of Service: Standard UK government website terms, allows automated access for public information
- **Priority:** High (2/5)
- **Rationale:** Primary official source for skilled worker visa information, regularly updated, easy to scrape

### 3. UK Immigration Rules - Official Guidance

- **Source Name:** UK Immigration Rules Official Guidance
- **Agency:** UK Home Office
- **URL:** https://www.gov.uk/guidance/immigration-rules
- **Visa Type:** Both (Student and Work)
- **Content Structure:** HTML with links to PDF documents
- **Access Method:** Direct URL, publicly accessible, may require navigation to specific rule sections
- **Update Frequency:** Updated when immigration rules change (typically several times per year)
- **Scraping Feasibility:** Moderate - HTML page with links to detailed PDF documents, may need to track multiple pages
- **Special Requirements:** None - No authentication required
- **Language:** English
- **Official Status:** ✅ Official UK Government source
- **Legal/Compliance:** 
  - Publicly accessible: Yes
  - robots.txt: Allows crawling (standard GOV.UK policy)
  - Terms of Service: Standard UK government website terms, allows automated access for public information
- **Priority:** High (3/5)
- **Rationale:** Comprehensive official immigration rules, authoritative source for policy changes, may require PDF fetcher for full content

### 4. UK Visas and Immigration - Visa Application Guidance

- **Source Name:** UK Visas and Immigration Application Guidance
- **Agency:** UK Visas and Immigration (UKVI)
- **URL:** https://www.gov.uk/browse/visas-immigration
- **Visa Type:** Both (Student and Work)
- **Content Structure:** HTML (directory/landing page with links to specific visa types)
- **Access Method:** Direct URL, publicly accessible, requires navigation to specific visa pages
- **Update Frequency:** Regular updates when guidance changes
- **Scraping Feasibility:** Moderate - Landing page with links, requires following links to specific visa pages
- **Special Requirements:** None - No authentication required
- **Language:** English
- **Official Status:** ✅ Official UK Government source
- **Legal/Compliance:** 
  - Publicly accessible: Yes
  - robots.txt: Allows crawling (standard GOV.UK policy)
  - Terms of Service: Standard UK government website terms, allows automated access for public information
- **Priority:** Medium (4/5)
- **Rationale:** Comprehensive directory of visa information, good for discovering new pages, but less direct than specific visa pages

### 5. UK Home Office - Policy Papers and Statements

- **Source Name:** UK Home Office Policy Papers and Statements
- **Agency:** UK Home Office
- **URL:** https://www.gov.uk/government/organisations/home-office (policy papers section)
- **Visa Type:** Both (Student and Work)
- **Content Structure:** HTML with links to PDF policy documents
- **Access Method:** Direct URL, publicly accessible, requires navigation to policy papers section
- **Update Frequency:** Updated when new policy papers are published (irregular, but important when they occur)
- **Scraping Feasibility:** Moderate to Difficult - Requires navigation, may need PDF fetcher for policy documents
- **Special Requirements:** None - No authentication required
- **Language:** English
- **Official Status:** ✅ Official UK Government source
- **Legal/Compliance:** 
  - Publicly accessible: Yes
  - robots.txt: Allows crawling (standard GOV.UK policy)
  - Terms of Service: Standard UK government website terms, allows automated access for public information
- **Priority:** Medium (5/5)
- **Rationale:** Important for major policy announcements, but less frequent updates, requires more complex scraping

## Prioritization Summary

### High Priority Sources (Top 3)

1. **UK Home Office - Student Visa Information Page** (Priority 1)
   - Direct, easy to scrape, regularly updated, primary source
   
2. **UK Home Office - Skilled Worker Visa Information Page** (Priority 2)
   - Direct, easy to scrape, regularly updated, primary source
   
3. **UK Immigration Rules - Official Guidance** (Priority 3)
   - Comprehensive, authoritative, may require PDF handling

### Medium Priority Sources

4. **UK Visas and Immigration - Visa Application Guidance** (Priority 4)
   - Good directory source, requires navigation
   
5. **UK Home Office - Policy Papers and Statements** (Priority 5)
   - Important for major changes, less frequent updates

## Legal/Compliance Summary

- ✅ All sources are publicly accessible
- ✅ robots.txt allows crawling (standard GOV.UK policy)
- ✅ Terms of Service permit automated access for public information
- ✅ All sources are official UK government websites
- ✅ No authentication required for any source
- ✅ No special restrictions or requirements identified

## Technical Assessment Summary

- **HTML Sources:** 5 (all can use existing HTML fetcher)
- **PDF Sources:** 2 (Immigration Rules and Policy Papers may link to PDFs)
- **Easy Scraping:** 2 sources (Student Visa, Skilled Worker Visa pages)
- **Moderate Scraping:** 3 sources (require navigation or PDF handling)
- **Difficult Scraping:** 0 sources

## Validation Results

- ✅ All URLs tested and accessible (2025-01-27)
- ✅ Content retrieval successful for all HTML pages
- ✅ No access issues identified
- ✅ All sources confirmed as current and active

## Implementation Notes

- Start with high-priority sources (1-3) for initial implementation
- Use existing HTML fetcher for direct pages (Student Visa, Skilled Worker Visa)
- May need to enhance fetcher to handle PDF links from Immigration Rules page
- Consider implementing navigation following for directory-style pages if needed
- All sources use standard GOV.UK structure, should be consistent to scrape

## Fetcher Naming Convention

Following the established pattern: `{country}_{agency}_{visa_type}.py`

Examples:
- `uk_home_office_student.py` - For Student Visa page
- `uk_home_office_work.py` - For Skilled Worker Visa page
- `uk_home_office_immigration_rules.py` - For Immigration Rules (both visa types)

## Next Steps

1. Implement fetchers for high-priority sources (1-3)
2. Test content extraction and change detection
3. Add sources to database using source configuration
4. Monitor for policy changes and validate detection
5. Consider adding medium-priority sources based on monitoring needs

