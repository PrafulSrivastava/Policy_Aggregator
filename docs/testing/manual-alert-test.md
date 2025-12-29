# Manual Alert System Testing Guide

This guide provides step-by-step instructions for manually testing the complete alert system end-to-end, from source change detection to email delivery.

## Prerequisites

1. **Environment Setup:**
   - Application running locally or in staging environment
   - Database configured and accessible
   - Email service (Resend) configured with valid API key
   - Admin user account created

2. **Test Email Address:**
   - Use a real email address you can access (e.g., Gmail, Outlook)
   - Recommended: Use a dedicated test email address for testing
   - Ensure email address can receive emails from your configured `EMAIL_FROM_ADDRESS`

3. **Required Environment Variables:**
   ```bash
   DATABASE_URL=postgresql://user:password@host:port/database
   JWT_SECRET_KEY=your-secret-key
   RESEND_API_KEY=your-resend-api-key
   EMAIL_FROM_ADDRESS=alerts@yourdomain.com
   ADMIN_UI_URL=http://localhost:8000
   ```

## Test Procedure

### Step 1: Create Test Route Subscription

1. **Via API (using curl or Postman):**
   ```bash
   # First, authenticate to get JWT token
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "your-password"}'
   
   # Create route subscription (use token from login response)
   curl -X POST http://localhost:8000/api/routes \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{
       "origin_country": "IN",
       "destination_country": "DE",
       "visa_type": "Student",
       "email": "your-test-email@example.com",
       "is_active": true
     }'
   ```

2. **Via Admin UI:**
   - Navigate to `http://localhost:8000`
   - Log in with admin credentials
   - Go to "Routes" section
   - Click "Add Route"
   - Fill in route details:
     - Origin Country: `IN`
     - Destination Country: `DE`
     - Visa Type: `Student`
     - Email: `your-test-email@example.com`
   - Click "Save"

3. **Verify Route Created:**
   ```bash
   curl -X GET http://localhost:8000/api/routes \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

### Step 2: Create Test Source

1. **Via API:**
   ```bash
   curl -X POST http://localhost:8000/api/sources \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{
       "country": "DE",
       "visa_type": "Student",
       "url": "https://example.com/germany-student-visa",
       "name": "Germany Student Visa Test Source",
       "fetch_type": "html",
       "check_frequency": "daily",
       "is_active": true,
       "metadata": {}
     }'
   ```

2. **Via Admin UI:**
   - Navigate to "Sources" section
   - Click "Add Source"
   - Fill in source details:
     - Country: `DE`
     - Visa Type: `Student`
     - URL: `https://example.com/germany-student-visa`
     - Name: `Germany Student Visa Test Source`
     - Fetch Type: `html`
     - Check Frequency: `daily`
   - Click "Save"

3. **Verify Source Created:**
   ```bash
   curl -X GET http://localhost:8000/api/sources \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

### Step 3: Trigger First Fetch (Baseline)

1. **Via API:**
   ```bash
   # Get source ID from previous step
   curl -X POST http://localhost:8000/api/sources/{SOURCE_ID}/trigger \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

2. **Verify First Fetch:**
   - Check response: `changeDetected` should be `false` (first fetch, no previous version)
   - Check database: PolicyVersion should be created
   - Check logs: Should see successful fetch message

### Step 4: Simulate Content Change

To test the alert system, you need to simulate a change in the source content. There are several approaches:

**Option A: Use a Test Source with Controllable Content**
- Use a test URL that you control (e.g., a simple HTML page you can modify)
- Update the content between fetches

**Option B: Use Mock Fetcher (Development Only)**
- Temporarily modify a fetcher to return different content on second call
- **Note:** This is for development/testing only, not production

**Option C: Use Real Source with Known Changes**
- Use a real government source that you know has changed recently
- Trigger fetch and verify change detection

### Step 5: Trigger Second Fetch (Change Detection)

1. **Via API:**
   ```bash
   # Trigger fetch again (after content change)
   curl -X POST http://localhost:8000/api/sources/{SOURCE_ID}/trigger \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

2. **Verify Change Detected:**
   - Check response: `changeDetected` should be `true`
   - Check response: `policyChangeId` should be present
   - Check database: PolicyChange should be created
   - Check logs: Should see "Change detected" message

### Step 6: Verify Email Sent

1. **Check Email Inbox:**
   - Open your test email inbox
   - Look for email with subject: `Policy Change Detected: IN → DE, Student Visa - Germany Student Visa Test Source`
   - Email should arrive within a few seconds

2. **Verify Email Content:**
   - **Subject Line:** Should include route and source information
   - **Route Information:** Should show origin → destination, visa type
   - **Source Information:** Should show source name and URL
   - **Timestamp:** Should show when change was detected
   - **Diff Preview:** Should show preview of changes (first 500 chars or 20 lines)
   - **View Full Diff Link:** Should link to admin UI with change ID
   - **Disclaimer:** Should include "This is information, not legal advice"

3. **Check EmailAlert Record:**
   ```bash
   # Query database or check via admin UI
   # EmailAlert should be created with status="sent"
   ```

### Step 7: Verify Full Diff Link

1. **Click "View Full Diff" link in email**
   - Should navigate to admin UI
   - Should show full diff of policy changes
   - Should display all change details

2. **Verify Admin UI:**
   - Navigate to `http://localhost:8000/policy-changes/{CHANGE_ID}`
   - Should display complete change information
   - Should show full diff text

## Testing Multiple Routes

### Test: Multiple Routes Matching One Source

1. Create multiple route subscriptions with same destination/visa type:
   - Route 1: `user1@example.com`
   - Route 2: `user2@example.com`
   - Route 3: `user3@example.com`

2. Trigger fetch with change for matching source

3. Verify:
   - All three email addresses receive emails
   - Each email is personalized for that route
   - Each route gets exactly one email

### Test: Route with No Matching Sources

1. Create route subscription:
   - Destination: `FR` (France)
   - Visa Type: `Work`

2. Create source:
   - Country: `DE` (Germany)
   - Visa Type: `Student`

3. Trigger fetch with change for source

4. Verify:
   - No email sent to route (different country/visa type)
   - No false alerts

## Testing Error Scenarios

### Test: Email Service Failure

1. Temporarily disable or misconfigure email service (e.g., invalid API key)

2. Trigger fetch with change

3. Verify:
   - Error handled gracefully
   - No application crash
   - Error logged appropriately
   - EmailAlert record created with status="failed"

### Test: Source Fetch Failure

1. Create source with invalid URL or network issue

2. Trigger fetch

3. Verify:
   - Error handled gracefully
   - No false alerts sent
   - Error logged appropriately
   - Failure tracked in error tracking system

## Testing Scheduled Job

### Test: Daily Fetch Job

1. **Via GitHub Actions (if configured):**
   - Go to GitHub Actions tab
   - Manually trigger "Daily Fetch Job" workflow
   - Monitor workflow logs

2. **Via Local Script:**
   ```bash
   python scripts/run_daily_fetch_job.py
   ```

3. **Verify:**
   - Job processes all active sources with `check_frequency="daily"`
   - Job handles errors gracefully
   - Job logs appropriately
   - Job triggers alerts when changes detected
   - Job summary shows sources processed, changes detected, alerts sent

## Troubleshooting

### Email Not Received

1. **Check Email Service Configuration:**
   - Verify `RESEND_API_KEY` is set correctly
   - Verify `EMAIL_FROM_ADDRESS` is verified in Resend
   - Check Resend dashboard for email status

2. **Check Application Logs:**
   - Look for email sending errors
   - Check if email service is available
   - Verify email address format

3. **Check Spam Folder:**
   - Email might be in spam/junk folder
   - Check email filters

4. **Check Database:**
   - Verify EmailAlert record created
   - Check status field (sent/failed)
   - Check error_message field if failed

### Change Not Detected

1. **Check Source Content:**
   - Verify source content actually changed
   - Check if content normalization is working
   - Verify hash comparison logic

2. **Check Database:**
   - Verify PolicyVersion records created
   - Check content_hash values
   - Verify PolicyChange record creation logic

3. **Check Logs:**
   - Look for change detection messages
   - Check for normalization errors
   - Verify hash generation

### Route Not Matching Source

1. **Check Route Configuration:**
   - Verify `destination_country` matches source `country`
   - Verify `visa_type` matches source `visa_type`
   - Verify route is active (`is_active=true`)

2. **Check Source Configuration:**
   - Verify source is active (`is_active=true`)
   - Verify source country and visa_type are correct

3. **Check Route Mapper:**
   - Verify route-to-source mapping logic
   - Check logs for mapping messages

## Test Checklist

- [ ] Route subscription created successfully
- [ ] Source created successfully
- [ ] First fetch completed (baseline established)
- [ ] Content change simulated
- [ ] Second fetch completed (change detected)
- [ ] PolicyChange record created in database
- [ ] Email received in test inbox
- [ ] Email content includes all required fields:
  - [ ] Route information (origin → destination, visa_type)
  - [ ] Source name and URL
  - [ ] Timestamp
  - [ ] Diff preview
  - [ ] Link to full diff
  - [ ] Disclaimer
- [ ] EmailAlert record created with status="sent"
- [ ] Full diff link works correctly
- [ ] Multiple routes test: all routes receive emails
- [ ] No matching routes test: no false alerts
- [ ] Error scenarios handled gracefully
- [ ] Scheduled job executes successfully

## Additional Notes

- **Test Data Cleanup:** After testing, consider cleaning up test routes and sources
- **Rate Limiting:** Be aware of email service rate limits during testing
- **Production Testing:** Never test with production data or real user email addresses
- **Logging:** Enable DEBUG logging for detailed troubleshooting information

## Support

For issues or questions:
1. Check application logs
2. Review error messages in database (EmailAlert.error_message)
3. Check Resend dashboard for email delivery status
4. Review GitHub Issues or contact development team

