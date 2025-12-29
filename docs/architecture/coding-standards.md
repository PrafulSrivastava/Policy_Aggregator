# Coding Standards

This section defines MINIMAL but CRITICAL standards for AI agents. These rules prevent common mistakes and ensure consistency across the codebase.

### Critical Fullstack Rules

**Environment Variables:** Always access environment variables through the config module (`api.config.settings`), never use `os.getenv()` or `os.environ` directly.

**Database Access:** Always use the Repository pattern. Never write raw SQL queries or access the database session directly from service/route layers.

**Error Handling:** All API routes must use FastAPI's exception handlers. Never return error responses directly - raise HTTPException or custom exceptions.

**Type Hints:** All Python functions must have type hints. Use `typing` module for complex types, Pydantic models for request/response validation.

**Async/Await:** Use `async def` and `await` for all database operations and external API calls. Never mix sync and async code without proper handling.

**Authentication:** All protected routes must use the `get_current_user` dependency. Never manually parse JWT tokens in route handlers.

**Pydantic Models:** All API request/response bodies must use Pydantic models. Never use raw dictionaries or `dict` type hints.

**Database Models:** All database models must inherit from SQLAlchemy `Base` and use the shared session factory. Never create new database connections manually.

**Fetcher Interface:** All source fetchers must implement the `SourceFetcher` interface. Never bypass the fetcher manager.

**Change Detection:** Always use the `ChangeDetector` service for detecting policy changes. Never compare content directly or use custom hashing logic.

**Email Sending:** Always use the `AlertEngine` service for sending emails. Never call Resend API directly from route handlers or services.

**Logging:** Use Python's `logging` module with appropriate log levels. Never use `print()` statements in production code.

**Configuration:** All configuration must be externalized to environment variables. Never hardcode URLs, API keys, or secrets.

**Template Rendering:** All Jinja2 templates must be rendered through FastAPI's `templates` dependency. Never render templates manually.

**API Responses:** All API responses must follow the standard format (success/error). Never return inconsistent response structures.

**Database Migrations:** Always use Alembic for schema changes. Never modify the database schema manually or write raw DDL.

**Testing:** All new features must include unit tests for critical logic. Integration tests required for new API endpoints.

### Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| **Components** | PascalCase | - | `UserProfile.html` (Jinja2 template) |
| **Templates** | snake_case | - | `route_list.html`, `change_detail.html` |
| **API Routes** | - | kebab-case | `/api/route-subscriptions`, `/api/policy-changes` |
| **Database Tables** | - | snake_case | `route_subscriptions`, `policy_versions` |
| **Python Files** | - | snake_case | `change_detector.py`, `source_repository.py` |
| **Python Classes** | - | PascalCase | `ChangeDetector`, `SourceRepository` |
| **Python Functions** | - | snake_case | `detect_change()`, `fetch_source()` |
| **Python Variables** | - | snake_case | `source_id`, `content_hash` |
| **Constants** | - | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_PAGE_SIZE` |
| **Environment Variables** | - | UPPER_SNAKE_CASE | `DATABASE_URL`, `JWT_SECRET_KEY` |
| **CSS Classes** | - | Tailwind utilities | `bg-blue-500`, `text-center` |
| **JavaScript Functions** | camelCase | - | `fetchRoutes()`, `handleSubmit()` |

### Code Organization

**File Structure:**
- One class per file (except for small related classes)
- Related functions grouped in modules
- Clear separation between layers (routes, services, repositories)

**Import Organization:**
```python
# Standard library imports
import asyncio
from datetime import datetime
from typing import Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

# Local imports
from api.database import get_db
from api.models.db.source import Source
from api.services.change_detector import ChangeDetector
```

**Function Length:**
- Functions should be < 50 lines
- Break down complex functions into smaller helper functions
- Use descriptive function names

**Class Design:**
- Single Responsibility Principle
- Use dependency injection (FastAPI's `Depends`)
- Avoid deep inheritance hierarchies

### Documentation Standards

**Docstrings:**
- All public functions and classes must have docstrings
- Use Google-style docstrings
- Include parameter descriptions and return types

**Example:**
```python
def detect_change(
    source_id: str,
    new_hash: str,
    new_content: str,
    previous_hash: Optional[str] = None
) -> ChangeDetectionResult:
    """
    Detect if policy content has changed by comparing hashes.
    
    Args:
        source_id: UUID of the source being checked
        new_hash: SHA256 hash of the new content
        new_content: Normalized text content
        previous_hash: Hash of previous version (None if first check)
    
    Returns:
        ChangeDetectionResult with change_detected flag and details
    
    Raises:
        ValueError: If source_id is invalid
    """
    # Implementation
```

**Comments:**
- Use comments to explain "why", not "what"
- Avoid obvious comments
- Document complex algorithms or business logic

### Git Commit Standards

**Commit Messages:**
- Use present tense: "Add route subscription endpoint"
- Be descriptive: "Fix change detection for empty content"
- Reference issues: "Fix #123: Handle null previous_hash"

**Branch Naming:**
- Feature: `feature/add-route-subscription`
- Bugfix: `fix/change-detection-edge-case`
- Refactor: `refactor/normalize-content`

### Python-Specific Standards

**Type Hints:**
- Always use type hints for function parameters and return types
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` from `typing` module

**Async Code:**
- Use `async def` for async functions
- Use `await` for async operations
- Never use `asyncio.run()` in async contexts

**Error Handling:**
- Use specific exception types
- Don't catch generic `Exception` unless necessary
- Always log errors before raising

**String Formatting:**
- Use f-strings for string interpolation
- Use `.format()` for complex formatting
- Avoid `%` formatting

---
