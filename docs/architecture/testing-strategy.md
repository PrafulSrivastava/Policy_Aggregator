# Testing Strategy

This section defines the comprehensive testing approach for the fullstack application, ensuring reliability, correctness, and maintainability.

### Testing Pyramid

```
        E2E Tests (Manual)
           /      \
    Integration Tests
      /            \
Frontend Unit    Backend Unit
```

**Testing Philosophy:**
- **Unit Tests:** Fast, isolated tests for individual functions/components
- **Integration Tests:** Test component interactions and API endpoints
- **E2E Tests:** Manual testing for MVP (admin UI is simple)

**Coverage Goals:**
- **Backend Unit Tests:** >80% coverage on critical paths (change detection, hashing, normalization)
- **Integration Tests:** All API endpoints tested
- **Frontend Tests:** Manual testing sufficient for MVP
- **E2E Tests:** Manual user acceptance testing

### Test Organization

#### Frontend Tests

**Structure:**
```
tests/
└── frontend/ (Manual testing for MVP)
    ├── test_scenarios.md  # Manual test scenarios
    └── test_checklist.md   # Test checklist
```

**MVP Approach:** Manual testing only
- **Rationale:** Server-side rendered templates, minimal JavaScript, simple admin interface
- **Test Scenarios:** Documented manual test cases for each screen
- **Future:** Can add Playwright/Cypress for automated E2E tests if needed

**Manual Test Scenarios:**
1. Login flow (valid/invalid credentials)
2. Dashboard display (stats, recent changes, system health)
3. Route subscription CRUD (create, view, delete)
4. Source configuration CRUD
5. Change history viewing and filtering
6. Change detail view with diff
7. Manual trigger functionality

#### Backend Tests

**Structure:**
```
tests/
├── unit/
│   ├── test_services/
│   │   ├── test_change_detector.py
│   │   ├── test_normalizer.py
│   │   ├── test_diff_generator.py
│   │   └── test_alert_engine.py
│   ├── test_repositories/
│   │   ├── test_source_repository.py
│   │   ├── test_policy_version_repository.py
│   │   └── test_route_subscription_repository.py
│   └── test_utils/
│       └── test_hashing.py
└── integration/
    ├── test_api/
    │   ├── test_routes.py
    │   ├── test_sources.py
    │   ├── test_changes.py
    │   └── test_auth.py
    ├── test_fetchers/
    │   └── test_fetcher_integration.py
    └── test_pipeline/
        └── test_end_to_end_pipeline.py
```

**Test Examples:**

**Backend Unit Test (Change Detector):**
```python
# tests/unit/test_services/test_change_detector.py
import pytest
from api.services.change_detector import ChangeDetector
from api.utils.hashing import generate_hash

@pytest.mark.asyncio
async def test_detect_change_when_hash_differs():
    """Test that change is detected when content hash differs."""
    detector = ChangeDetector()
    source_id = "test-source-id"
    old_content = "Original policy content"
    new_content = "Updated policy content"
    
    old_hash = generate_hash(old_content)
    new_hash = generate_hash(new_content)
    
    # Mock repository to return old version
    result = await detector.detect_change(
        source_id=source_id,
        new_hash=new_hash,
        new_content=new_content,
        previous_hash=old_hash
    )
    
    assert result.change_detected is True
    assert result.old_hash == old_hash
    assert result.new_hash == new_hash

@pytest.mark.asyncio
async def test_no_change_when_hash_matches():
    """Test that no change is detected when hash matches."""
    detector = ChangeDetector()
    source_id = "test-source-id"
    content = "Same policy content"
    content_hash = generate_hash(content)
    
    result = await detector.detect_change(
        source_id=source_id,
        new_hash=content_hash,
        new_content=content,
        previous_hash=content_hash
    )
    
    assert result.change_detected is False
```

**Backend Integration Test (API Endpoint):**
```python
# tests/integration/test_api/test_routes.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_create_route_subscription():
    """Test creating a route subscription via API."""
    # Login first
    response = client.post("/auth/login", json={
        "username": "admin",
        "password": "test_password"
    })
    token = response.json()["access_token"]
    
    # Create route subscription
    response = client.post(
        "/api/routes",
        json={
            "originCountry": "IN",
            "destinationCountry": "DE",
            "visaType": "Student",
            "email": "test@example.com"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["originCountry"] == "IN"
    assert data["destinationCountry"] == "DE"
    assert data["visaType"] == "Student"

def test_create_route_duplicate():
    """Test that duplicate route subscriptions are rejected."""
    # ... test implementation
```

#### E2E Tests

**MVP Approach:** Manual E2E testing

**E2E Test Scenarios:**
1. **Full Pipeline Test:**
   - Configure source
   - Trigger manual fetch
   - Verify change detection
   - Verify email alert sent
   - Verify change appears in admin UI

2. **Route Subscription Flow:**
   - Create route subscription
   - Verify source association
   - Trigger fetch
   - Verify alert sent to correct email

3. **Error Handling Flow:**
   - Configure invalid source URL
   - Trigger fetch
   - Verify error handling and logging

**Future:** Can add Playwright for automated E2E tests:
```python
# tests/e2e/test_user_flows.py (Future)
from playwright.sync_api import Page

def test_create_route_subscription_flow(page: Page):
    page.goto("http://localhost:8000/login")
    page.fill("#username", "admin")
    page.fill("#password", "password")
    page.click("button[type='submit']")
    
    page.goto("http://localhost:8000/routes")
    page.click("text=Add New Route")
    # ... continue test
```

### Test Examples

#### Frontend Component Test (Future)

For MVP, frontend uses server-side rendering, so component tests aren't applicable. If migrating to React/SPA:

```typescript
// tests/frontend/components/Button.test.tsx (Future)
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

test('renders button with text', () => {
  render(<Button text="Save" variant="primary" />);
  expect(screen.getByText('Save')).toBeInTheDocument();
});

test('shows loading state', () => {
  render(<Button text="Save" loading={true} />);
  expect(screen.getByText('Loading...')).toBeInTheDocument();
});
```

#### Backend API Test

```python
# tests/integration/test_api/test_sources.py
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.database import get_db
from tests.fixtures.sample_data import create_test_source

client = TestClient(app)

@pytest.fixture
def auth_token():
    """Get authentication token for tests."""
    response = client.post("/auth/login", json={
        "username": "admin",
        "password": "test_password"
    })
    return response.json()["access_token"]

def test_list_sources(auth_token):
    """Test listing all sources."""
    response = client.get(
        "/api/sources",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()

def test_create_source(auth_token):
    """Test creating a new source."""
    response = client.post(
        "/api/sources",
        json={
            "country": "DE",
            "visaType": "Student",
            "url": "https://example.com/policy",
            "fetchType": "html",
            "checkFrequency": "daily",
            "name": "Test Source"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["country"] == "DE"
    assert data["name"] == "Test Source"
```

#### E2E Pipeline Test

```python
# tests/integration/test_pipeline/test_end_to_end_pipeline.py
import pytest
from api.services.fetcher_manager import FetcherManager
from api.services.change_detector import ChangeDetector
from api.services.alert_engine import AlertEngine

@pytest.mark.asyncio
async def test_full_pipeline():
    """Test complete pipeline: fetch → normalize → detect → alert."""
    # Setup: Create test source and route subscription
    source = await create_test_source()
    route = await create_test_route_subscription()
    
    # Step 1: Fetch source
    fetcher_manager = FetcherManager()
    fetch_result = await fetcher_manager.fetch_source(source.id)
    assert fetch_result.success is True
    
    # Step 2: Detect change
    change_detector = ChangeDetector()
    change_result = await change_detector.detect_change(
        source_id=source.id,
        new_hash=fetch_result.content_hash,
        new_content=fetch_result.normalized_text
    )
    
    # Step 3: Send alert (if change detected)
    if change_result.change_detected:
        alert_engine = AlertEngine()
        await alert_engine.send_change_alert(change_result.policy_change_id)
        
        # Verify alert sent
        alerts = await get_email_alerts_for_change(change_result.policy_change_id)
        assert len(alerts) > 0
```

### Test Data and Fixtures

**Test Fixtures:**
```python
# tests/fixtures/sample_data.py
import pytest
from api.models.db.source import Source
from api.models.db.route_subscription import RouteSubscription

@pytest.fixture
async def test_source(db_session):
    """Create a test source."""
    source = Source(
        country="DE",
        visa_type="Student",
        url="https://example.com/policy",
        fetch_type="html",
        check_frequency="daily",
        name="Test Source"
    )
    db_session.add(source)
    await db_session.commit()
    return source

@pytest.fixture
async def test_route_subscription(db_session):
    """Create a test route subscription."""
    route = RouteSubscription(
        origin_country="IN",
        destination_country="DE",
        visa_type="Student",
        email="test@example.com"
    )
    db_session.add(route)
    await db_session.commit()
    return route
```

### Test Execution

**Running Tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov=fetchers --cov-report=html

# Run specific test file
pytest tests/unit/test_services/test_change_detector.py

# Run with verbose output
pytest -v

# Run only integration tests
pytest tests/integration/

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto
```

**CI/CD Integration:**
- Tests run automatically on every pull request
- Tests must pass before merge
- Coverage reports uploaded to codecov
- Failed tests block deployment

---
