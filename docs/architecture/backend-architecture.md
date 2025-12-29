# Backend Architecture

This section defines backend-specific architecture details. The backend is a monolithic FastAPI application with serverless-friendly design (can be deployed as serverless functions later if needed, but MVP uses traditional server deployment).

### Service Architecture

The backend follows a layered architecture: Routes → Services → Repositories → Database. This separation enables testing, maintainability, and future refactoring.

#### Controller/Route Organization

**FastAPI Route Structure:**

```
api/
├── routes/
│   ├── __init__.py
│   ├── api.py              # REST API routes (/api/*)
│   ├── web.py               # Web page routes (HTML rendering)
│   ├── auth.py              # Authentication routes (/auth/*)
│   └── health.py            # Health check route
├── services/
│   ├── __init__.py
│   ├── fetcher_manager.py   # Source fetcher orchestration
│   ├── normalizer.py        # Content normalization
│   ├── change_detector.py   # Change detection logic
│   ├── diff_generator.py    # Diff generation
│   ├── alert_engine.py      # Email alert sending
│   └── dashboard.py         # Dashboard statistics
├── repositories/
│   ├── __init__.py
│   ├── source_repository.py
│   ├── policy_version_repository.py
│   ├── policy_change_repository.py
│   ├── route_subscription_repository.py
│   ├── email_alert_repository.py
│   └── user_repository.py
├── models/
│   ├── __init__.py
│   ├── db/                  # SQLAlchemy database models
│   │   ├── source.py
│   │   ├── policy_version.py
│   │   ├── policy_change.py
│   │   ├── route_subscription.py
│   │   ├── email_alert.py
│   │   └── user.py
│   └── schemas/             # Pydantic request/response models
│       ├── source.py
│       ├── policy_version.py
│       ├── policy_change.py
│       ├── route_subscription.py
│       └── user.py
├── middleware/
│   ├── __init__.py
│   ├── auth.py              # Authentication middleware
│   └── error_handler.py     # Global error handling
├── utils/
│   ├── __init__.py
│   ├── hashing.py           # SHA256 hash utilities
│   └── logging.py           # Logging configuration
└── main.py                  # FastAPI application entry point
```

**Controller Template Example:**

```python
# api/routes/api.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from api.models.schemas.route_subscription import RouteSubscriptionCreate, RouteSubscriptionResponse
from api.services.route_service import RouteService
from api.middleware.auth import get_current_user

router = APIRouter(prefix="/api", tags=["routes"])

@router.get("/routes", response_model=List[RouteSubscriptionResponse])
async def list_routes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """List all route subscriptions with pagination."""
    service = RouteService()
    return await service.list_routes(page=page, page_size=page_size)

@router.post("/routes", response_model=RouteSubscriptionResponse, status_code=201)
async def create_route(
    route_data: RouteSubscriptionCreate,
    current_user = Depends(get_current_user)
):
    """Create a new route subscription."""
    service = RouteService()
    try:
        return await service.create_route(route_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=409, detail="Route subscription already exists")

@router.delete("/routes/{route_id}", status_code=204)
async def delete_route(
    route_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a route subscription."""
    service = RouteService()
    route = await service.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route subscription not found")
    await service.delete_route(route_id)
    return None
```

**Key Patterns:**
- **Dependency Injection:** Services injected via FastAPI's dependency system
- **Pydantic Models:** Request/response validation via Pydantic schemas
- **Error Handling:** HTTPException for API errors, proper status codes
- **Authentication:** All routes protected via `get_current_user` dependency

### Database Architecture

The backend uses SQLAlchemy ORM with Alembic for migrations. Repository pattern abstracts database operations.

#### Schema Design

Database schema defined in SQLAlchemy models (see Database Schema section for DDL). Models use declarative base:

```python
# api/models/db/source.py
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from api.database import Base
import uuid

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country = Column(String(2), nullable=False)
    visa_type = Column(String(50), nullable=False)
    url = Column(String, nullable=False)
    fetch_type = Column(String(10), nullable=False)  # 'html' or 'pdf'
    check_frequency = Column(String(20), nullable=False)  # 'daily', 'weekly', 'custom'
    name = Column(String(255), nullable=False)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_change_detected_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    metadata = Column(JSONB, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

#### Data Access Layer

Repository pattern provides clean abstraction:

```python
# api/repositories/source_repository.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.models.db.source import Source

class SourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, source_data: dict) -> Source:
        """Create a new source."""
        source = Source(**source_data)
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return source
    
    async def get_by_id(self, source_id: str) -> Optional[Source]:
        """Get source by ID."""
        result = await self.session.execute(
            select(Source).where(Source.id == source_id)
        )
        return result.scalar_one_or_none()
    
    async def list_active(self) -> List[Source]:
        """List all active sources."""
        result = await self.session.execute(
            select(Source).where(Source.is_active == True)
        )
        return result.scalars().all()
    
    async def update_last_checked(self, source_id: str, timestamp: datetime):
        """Update last checked timestamp."""
        source = await self.get_by_id(source_id)
        if source:
            source.last_checked_at = timestamp
            await self.session.commit()
```

**Key Patterns:**
- **Async/Await:** All database operations are async for performance
- **Session Management:** Database session injected via dependency
- **Type Hints:** Full type hints for better IDE support and documentation
- **Error Handling:** Repository methods raise exceptions, handled by service layer

### Authentication Architecture

Simple JWT-based authentication for single admin user. Can be extended for multi-user support later.

#### Auth Flow

```python
# api/auth/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from api.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user and return User object if valid."""
    user_repo = UserRepository(get_db_session())
    user = await user_repo.get_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
```

#### Middleware/Guards

```python
# api/middleware/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from api.repositories.user_repository import UserRepository

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> User:
    """Dependency to get current authenticated user."""
    token = credentials.credentials if credentials else None
    
    # Also check cookie for web requests
    if not token and request:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_repo = UserRepository(get_db_session())
    user = await user_repo.get_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

**Key Design Decisions:**
- **JWT Tokens:** Stateless authentication, 24-hour expiration
- **Bcrypt Hashing:** Secure password storage
- **Cookie Support:** Tokens in cookies for web requests, Bearer header for API
- **Single User:** Simple structure, can extend for multi-user later

---
