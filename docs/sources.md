# Policy Sources - India → Germany Route

This document lists all configured policy sources for monitoring India → Germany immigration routes.

## Overview

We monitor **5 official Germany immigration policy sources** covering Student and Work visa categories for the India → Germany route.

## Source List

### 1. Germany BMI Student Visa Information

- **Source Name:** Germany BMI Student Visa Information
- **Agency:** Bundesministerium des Innern (BMI) - Federal Ministry of the Interior
- **URL:** https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/student-visa.html
- **Visa Type:** Student
- **Fetch Type:** HTML
- **Fetcher:** `de_bmi_student.py`
- **What it Monitors:** Official student visa requirements, policy changes, and application procedures for India → Germany route
- **Check Frequency:** Daily
- **Status:** Active

### 2. Germany BMI Skilled Worker Visa Information

- **Source Name:** Germany BMI Skilled Worker Visa Information
- **Agency:** Bundesministerium des Innern (BMI) - Federal Ministry of the Interior
- **URL:** https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/skilled-workers.html
- **Visa Type:** Work
- **Fetch Type:** HTML
- **Fetcher:** `de_bmi_work.py`
- **What it Monitors:** Official skilled worker visa requirements, policy changes, and application procedures for India → Germany route
- **Check Frequency:** Daily
- **Status:** Active

### 3. Germany Auswärtiges Amt Student Visa Information

- **Source Name:** Germany Auswärtiges Amt Student Visa Information
- **Agency:** Auswärtiges Amt - Federal Foreign Office
- **URL:** https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-students
- **Visa Type:** Student
- **Fetch Type:** HTML
- **Fetcher:** `de_auswaertiges_amt_student.py`
- **What it Monitors:** Official Foreign Office student visa requirements and policy information for India → Germany route
- **Check Frequency:** Daily
- **Status:** Active

### 4. Germany Auswärtiges Amt Work Visa Information

- **Source Name:** Germany Auswärtiges Amt Work Visa Information
- **Agency:** Auswärtiges Amt - Federal Foreign Office
- **URL:** https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-employment
- **Visa Type:** Work
- **Fetch Type:** HTML
- **Fetcher:** `de_auswaertiges_amt_work.py`
- **What it Monitors:** Official Foreign Office work visa requirements and policy information for India → Germany route
- **Check Frequency:** Daily
- **Status:** Active

### 5. Make it in Germany Skilled Worker Visa Information

- **Source Name:** Make it in Germany Skilled Worker Visa Information
- **Agency:** Make it in Germany (Official Government Portal)
- **URL:** https://www.make-it-in-germany.com/en/visa/skilled-workers
- **Visa Type:** Work
- **Fetch Type:** HTML
- **Fetcher:** `de_make_it_in_germany_work.py`
- **What it Monitors:** Official Make it in Germany portal for skilled worker visa information and policy changes for India → Germany route
- **Check Frequency:** Daily
- **Status:** Active

## Summary

- **Total Sources:** 5
- **Student Visa Sources:** 2
- **Work Visa Sources:** 3
- **HTML Sources:** 5
- **PDF Sources:** 0
- **Route:** India → Germany

## Notes

- All sources are official German government websites
- URLs may need to be updated if government websites are restructured
- Some sources may require periodic verification to ensure URLs remain valid
- All fetchers follow the plugin architecture and use standard HTML fetching utilities

## Adding New Sources

To add a new source:

1. Create a new fetcher file following the naming convention: `{country}_{agency}_{visa_type}.py`
2. Implement the `fetch()` function using `fetch_html()` or `fetch_pdf()` utilities
3. Add source configuration to `scripts/add_germany_sources.py`
4. Run the script to add the source to the database
5. Update this documentation

## Testing Sources

To test a source fetcher:

```python
from fetchers.de_bmi_student import fetch

result = fetch("https://www.bmi.bund.de/...", {
    "country": "DE",
    "visa_type": "Student",
    "fetch_type": "html"
})

print(f"Success: {result.success}")
print(f"Content length: {len(result.raw_text)}")
```

