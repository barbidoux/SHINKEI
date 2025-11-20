# 🚀 **SHINKEI - QUICK START GUIDE FOR CLAUDE CODE**

## **Practical Implementation Companion**
## **Version:** 1.0.0

---

# **HOW TO USE THIS GUIDE**

This document provides:
1. **Quick reference patterns** for common tasks
2. **Copy-paste templates** for repetitive code
3. **Debugging workflows** for common issues
4. **Decision trees** for architectural choices

**Use this alongside the main implementation plan for maximum efficiency.**

---

# **PART I: GETTING STARTED**

## **Daily Startup Checklist**

```bash
# 1. Pull latest changes
git pull origin develop

# 2. Start development environment
cd shinkei
docker-compose up -d

# 3. Wait for services to be healthy
docker-compose ps

# 4. Verify database is accessible
docker-compose exec postgres psql -U shinkei_user -d shinkei -c "SELECT 1"

# 5. Check backend health
curl http://localhost:8000/health

# 6. Check frontend dev server
curl http://localhost:5173

# 7. Run existing tests to ensure stability
cd backend && poetry run pytest
cd ../frontend && npm test

# ✅ Ready to code!
```

---

## **Creating a New Feature Branch**

```bash
# Pattern: feature/phase-X-milestone-Y-descriptive-name
git checkout develop
git pull
git checkout -b feature/phase-1-milestone-2-world-model
```

---

## **Common Code Patterns**

### **Pattern 1: Creating a New Model**

**Template:** `backend/src/shinkei/models/[entity_name].py`

```python
"""[EntityName] model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.shinkei.database.engine import Base
import uuid


class [EntityName](Base):
    """
    [EntityName] model representing [description].
    
    Attributes:
        id: Unique identifier
        [field_name]: [description]
    """
    __tablename__ = "[table_name]"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="[EntityName] UUID"
    )
    
    # Foreign keys
    [parent]_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("[parent_table].id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="[Parent] ID"
    )
    
    # Fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="[Description]"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp of creation"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp of last update"
    )
    
    # Relationships
    [parent]: Mapped["[Parent]"] = relationship("[Parent]", back_populates="[children]")
    
    def __repr__(self) -> str:
        return f"<[EntityName](id={self.id}, name={self.name})>"
```

**Checklist after creating model:**
- [ ] Add to `backend/src/shinkei/models/__init__.py`
- [ ] Create migration: `alembic revision --autogenerate -m "create_[table_name]_table"`
- [ ] Review migration file
- [ ] Apply migration: `alembic upgrade head`
- [ ] Create corresponding schema file
- [ ] Create repository file
- [ ] Write unit tests

---

### **Pattern 2: Creating a Schema**

**Template:** `backend/src/shinkei/schemas/[entity_name].py`

```python
"""[EntityName] Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class [EntityName]Base(BaseModel):
    """Base [entity] schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class [EntityName]Create([EntityName]Base):
    """Schema for creating a new [entity]."""
    pass


class [EntityName]Update(BaseModel):
    """Schema for updating a [entity]."""
    model_config = ConfigDict(extra='forbid')
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class [EntityName]Response([EntityName]Base):
    """Schema for [entity] responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    [parent]_id: str
    created_at: datetime
    updated_at: datetime


class [EntityName]ListResponse(BaseModel):
    """Schema for paginated [entity] list."""
    [entities]: list[[EntityName]Response]
    total: int
    page: int
    page_size: int
```

---

### **Pattern 3: Creating a Repository**

**Template:** `backend/src/shinkei/repositories/[entity_name].py`

```python
"""[EntityName] repository for database operations."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.models.[entity_name] import [EntityName]
from src.shinkei.schemas.[entity_name] import [EntityName]Create, [EntityName]Update
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


class [EntityName]Repository:
    """Repository for [EntityName] model database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(
        self,
        [parent]_id: str,
        data: [EntityName]Create
    ) -> [EntityName]:
        """
        Create a new [entity].
        
        Args:
            [parent]_id: [Parent] ID
            data: [Entity] creation data
            
        Returns:
            Created [entity] instance
        """
        entity = [EntityName](
            [parent]_id=[parent]_id,
            name=data.name,
            description=data.description,
        )
        
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        
        logger.info("[entity]_created", entity_id=entity.id)
        return entity
    
    async def get_by_id(self, entity_id: str) -> Optional[[EntityName]]:
        """Get [entity] by ID."""
        result = await self.session.execute(
            select([EntityName]).where([EntityName].id == entity_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_[parent](
        self,
        [parent]_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[[EntityName]], int]:
        """
        List [entities] by [parent].
        
        Args:
            [parent]_id: [Parent] ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of ([entities] list, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(func.count())
            .select_from([EntityName])
            .where([EntityName].[parent]_id == [parent]_id)
        )
        total = count_result.scalar_one()
        
        # Get entities
        result = await self.session.execute(
            select([EntityName])
            .where([EntityName].[parent]_id == [parent]_id)
            .order_by([EntityName].created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        entities = list(result.scalars().all())
        
        return entities, total
    
    async def update(
        self,
        entity_id: str,
        data: [EntityName]Update
    ) -> Optional[[EntityName]]:
        """Update [entity]."""
        entity = await self.get_by_id(entity_id)
        if not entity:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(entity, field, value)
        
        await self.session.flush()
        await self.session.refresh(entity)
        
        logger.info("[entity]_updated", entity_id=entity.id)
        return entity
    
    async def delete(self, entity_id: str) -> bool:
        """Delete [entity]."""
        entity = await self.get_by_id(entity_id)
        if not entity:
            return False
        
        await self.session.delete(entity)
        await self.session.flush()
        
        logger.info("[entity]_deleted", entity_id=entity_id)
        return True
```

---

### **Pattern 4: Creating API Endpoints**

**Template:** `backend/src/shinkei/api/v1/endpoints/[entities].py`

```python
"""[Entity] API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.auth.dependencies import get_current_active_user
from src.shinkei.auth.authorization import verify_[parent]_ownership
from src.shinkei.database.engine import get_db
from src.shinkei.models.user import User
from src.shinkei.repositories.[entity_name] import [EntityName]Repository
from src.shinkei.schemas.[entity_name] import (
    [EntityName]Create,
    [EntityName]Response,
    [EntityName]Update,
    [EntityName]ListResponse
)
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/[entities]", tags=["[entities]"])


@router.post(
    "",
    response_model=[EntityName]Response,
    status_code=status.HTTP_201_CREATED
)
async def create_[entity](
    [parent]_id: str,
    data: [EntityName]Create,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> [EntityName]Response:
    """Create a new [entity]."""
    
    # Verify [parent] ownership
    await verify_[parent]_ownership([parent]_id, current_user, session)
    
    repo = [EntityName]Repository(session)
    entity = await repo.create([parent]_id, data)
    
    logger.info("[entity]_created", entity_id=entity.id, user_id=current_user.id)
    return [EntityName]Response.model_validate(entity)


@router.get("", response_model=[EntityName]ListResponse)
async def list_[entities](
    [parent]_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> [EntityName]ListResponse:
    """List [entities]."""
    
    await verify_[parent]_ownership([parent]_id, current_user, session)
    
    repo = [EntityName]Repository(session)
    skip = (page - 1) * page_size
    
    entities, total = await repo.list_by_[parent](
        [parent]_id,
        skip=skip,
        limit=page_size
    )
    
    return [EntityName]ListResponse(
        [entities]=[[EntityName]Response.model_validate(e) for e in entities],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{entity_id}", response_model=[EntityName]Response)
async def get_[entity](
    entity_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> [EntityName]Response:
    """Get a specific [entity]."""
    
    repo = [EntityName]Repository(session)
    entity = await repo.get_by_id(entity_id)
    
    if not entity:
        raise HTTPException(status_code=404, detail="[Entity] not found")
    
    # Verify ownership through [parent]
    await verify_[parent]_ownership(entity.[parent]_id, current_user, session)
    
    return [EntityName]Response.model_validate(entity)


@router.put("/{entity_id}", response_model=[EntityName]Response)
async def update_[entity](
    entity_id: str,
    data: [EntityName]Update,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> [EntityName]Response:
    """Update a [entity]."""
    
    repo = [EntityName]Repository(session)
    entity = await repo.get_by_id(entity_id)
    
    if not entity:
        raise HTTPException(status_code=404, detail="[Entity] not found")
    
    await verify_[parent]_ownership(entity.[parent]_id, current_user, session)
    
    updated = await repo.update(entity_id, data)
    
    logger.info("[entity]_updated", entity_id=entity_id, user_id=current_user.id)
    return [EntityName]Response.model_validate(updated)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_[entity](
    entity_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> None:
    """Delete a [entity]."""
    
    repo = [EntityName]Repository(session)
    entity = await repo.get_by_id(entity_id)
    
    if not entity:
        raise HTTPException(status_code=404, detail="[Entity] not found")
    
    await verify_[parent]_ownership(entity.[parent]_id, current_user, session)
    
    await repo.delete(entity_id)
    
    logger.info("[entity]_deleted", entity_id=entity_id, user_id=current_user.id)
```

**Checklist after creating endpoints:**
- [ ] Add router to `backend/src/shinkei/api/v1/router.py`
- [ ] Write integration tests
- [ ] Test all CRUD operations manually
- [ ] Update OpenAPI documentation
- [ ] Add to Postman collection

---

### **Pattern 5: Writing Unit Tests**

**Template:** `backend/tests/unit/test_[component].py`

```python
"""Unit tests for [Component]."""
import pytest
from [imports]


@pytest.fixture
def [fixture_name]():
    """Fixture description."""
    return [setup_code]


def test_[feature]_[scenario]([fixtures]):
    """Test [what is being tested]."""
    # Arrange
    [setup]
    
    # Act
    result = [action]
    
    # Assert
    assert result == [expected]
    assert [condition]


@pytest.mark.asyncio
async def test_async_[feature]([fixtures]):
    """Test async [what is being tested]."""
    # Arrange
    [setup]
    
    # Act
    result = await [async_action]
    
    # Assert
    assert result is not None
```

---

### **Pattern 6: Writing Integration Tests**

**Template:** `backend/tests/integration/test_api_[entity].py`

```python
"""Integration tests for [Entity] API endpoints."""
import pytest
from httpx import AsyncClient
from src.shinkei.main import app


@pytest.fixture
def auth_headers(test_user):
    """Create authorization headers."""
    from src.shinkei.auth.jwt import create_test_token
    token = create_test_token(test_user.id, test_user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_[entity](auth_headers, test_[parent]):
    """Test creating a new [entity]."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/[entities]?[parent]_id={test_[parent].id}",
            json={
                "name": "Test [Entity]",
                "description": "Test description"
            },
            headers=auth_headers
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test [Entity]"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_[entities](auth_headers, test_[parent]):
    """Test listing [entities]."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/[entities]?[parent]_id={test_[parent].id}",
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "[entities]" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_[operation]_unauthorized():
    """Test [operation] without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/[entities]/some-id")
    
    assert response.status_code == 401
```

---

## **PART II: DEBUGGING WORKFLOWS**

### **Workflow 1: Database Query Not Working**

```bash
# 1. Check if migration is applied
cd backend
poetry run alembic current
poetry run alembic history

# 2. Check actual database schema
docker-compose exec postgres psql -U shinkei_user -d shinkei
\dt  # List tables
\d [table_name]  # Describe table

# 3. Test query directly in database
SELECT * FROM [table_name] LIMIT 5;

# 4. Check SQLAlchemy logs
# Add to config.py temporarily:
db_echo: bool = True

# 5. Check for foreign key violations
# Look for constraint errors in logs

# 6. Verify relationship configuration
# Check back_populates matches on both sides
```

---

### **Workflow 2: API Endpoint Returns 422 (Validation Error)**

```bash
# 1. Check request body matches schema
# Look at Pydantic validation error details

# 2. Verify schema field types
# Check optional vs required fields

# 3. Test with minimal valid payload
curl -X POST http://localhost:8000/api/v1/[endpoint] \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [token]" \
  -d '{"name": "test"}'

# 4. Check for extra fields if using ConfigDict(extra='forbid')

# 5. Verify enum values match schema
```

---

### **Workflow 3: Tests Failing After Change**

```bash
# 1. Run specific test with verbose output
poetry run pytest tests/unit/test_specific.py::test_function -v -s

# 2. Check test database is clean
# Tests should use fixtures that cleanup

# 3. Check for leftover state
# Look for global variables or cached data

# 4. Run tests in isolation
poetry run pytest tests/unit/test_specific.py -k test_one

# 5. Check fixture dependencies
# Ensure fixtures are properly scoped (function vs session)

# 6. Clear pytest cache
rm -rf .pytest_cache
find . -type d -name __pycache__ -exec rm -r {} +
```

---

### **Workflow 4: Import Errors**

```bash
# 1. Check package is installed
poetry show [package-name]

# 2. Reinstall dependencies
poetry install

# 3. Check Python path
poetry run python -c "import sys; print('\n'.join(sys.path))"

# 4. Check for circular imports
# Look at import order in error message

# 5. Verify __init__.py files exist

# 6. Check for typos in import statements
```

---

### **Workflow 5: Docker Service Not Starting**

```bash
# 1. Check logs
docker-compose logs [service-name]

# 2. Check if port is already in use
lsof -i :5432  # PostgreSQL
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# 3. Rebuild images
docker-compose build --no-cache [service-name]

# 4. Remove volumes and restart
docker-compose down -v
docker-compose up -d

# 5. Check disk space
df -h

# 6. Check Docker daemon status
docker info
```

---

## **PART III: DECISION TREES**

### **Decision Tree 1: Where Should This Logic Go?**

```
Is it database-related?
├─ Yes: Does it involve multiple tables?
│  ├─ Yes → Service layer
│  └─ No → Repository
└─ No: Does it involve business logic?
   ├─ Yes → Service layer
   └─ No: Is it API-specific?
      ├─ Yes → API endpoint
      └─ No → Utility function
```

### **Decision Tree 2: What Type of Test Should I Write?**

```
What am I testing?
├─ Single function/method → Unit test
├─ Database operation → Integration test
├─ API endpoint → Integration test
├─ User workflow → E2E test
└─ External service → Integration test with mocks
```

### **Decision Tree 3: How Should I Handle This Error?**

```
What type of error?
├─ Expected user error (bad input)
│  └─ Return 4xx HTTP status
├─ Resource not found
│  └─ Return 404 with clear message
├─ Authorization failure
│  └─ Return 403/404 (don't leak existence)
├─ External service failure
│  └─ Log + Return 503 + Retry logic
└─ Unexpected error
   └─ Log + Return 500 + Notify monitoring
```

---

## **PART IV: PERFORMANCE OPTIMIZATION CHECKLIST**

### **Database Performance**

- [ ] Add indexes to foreign keys
- [ ] Add indexes to frequently queried columns
- [ ] Use `select_in_load` for relationships
- [ ] Limit query results with pagination
- [ ] Use `scalar_one_or_none()` when expecting one result
- [ ] Avoid N+1 queries with `selectinload()`
- [ ] Use database-level constraints
- [ ] Regular VACUUM and ANALYZE on PostgreSQL

### **API Performance**

- [ ] Use async/await properly
- [ ] Implement response caching for read-heavy endpoints
- [ ] Use compression (gzip) for responses
- [ ] Paginate list endpoints
- [ ] Use HTTP caching headers
- [ ] Implement rate limiting
- [ ] Profile slow endpoints with middleware

### **Frontend Performance**

- [ ] Lazy load routes
- [ ] Implement virtual scrolling for long lists
- [ ] Cache API responses
- [ ] Debounce user input
- [ ] Optimize images
- [ ] Use SvelteKit's SSR when appropriate
- [ ] Minimize bundle size

---

## **PART V: SECURITY CHECKLIST**

### **Every API Endpoint Must:**

- [ ] Require authentication (unless intentionally public)
- [ ] Validate all input data
- [ ] Check resource ownership
- [ ] Log access attempts
- [ ] Return appropriate error codes (don't leak info)
- [ ] Use parameterized queries (SQLAlchemy handles this)
- [ ] Rate limit sensitive operations
- [ ] Sanitize error messages

### **Every Database Operation Must:**

- [ ] Use SQLAlchemy ORM (no raw SQL)
- [ ] Validate foreign key constraints
- [ ] Use transactions appropriately
- [ ] Not expose internal IDs in URLs (use UUIDs)
- [ ] Log all modifications
- [ ] Handle concurrent updates

### **Every User Input Must:**

- [ ] Be validated by Pydantic schema
- [ ] Have length limits
- [ ] Be sanitized for XSS (frontend)
- [ ] Be checked against business rules
- [ ] Be logged (without PII)

---

## **PART VI: COMMIT MESSAGE CONVENTION**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semi-colons, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Changes to build process or auxiliary tools

**Examples:**
```
feat(world): add world creation endpoint

Implements POST /api/v1/worlds with full validation and tests.
Includes authorization check and database transaction handling.

Closes #42

---

fix(auth): correct JWT expiration validation

The JWT validation was not properly checking expiration time.
Now uses proper datetime comparison with timezone awareness.

Fixes #58

---

test(story-beat): add integration tests for beat generation

Adds comprehensive integration tests for the beat generation pipeline,
including mocking of AI model responses.
```

---

## **PART VII: QUICK REFERENCE COMMANDS**

### **Backend Commands**

```bash
# Development
poetry run uvicorn src.shinkei.main:app --reload --host 0.0.0.0 --port 8000

# Testing
poetry run pytest                           # All tests
poetry run pytest tests/unit/              # Unit tests only
poetry run pytest tests/integration/       # Integration tests only
poetry run pytest -v -s                    # Verbose with print statements
poetry run pytest --cov                    # With coverage
poetry run pytest -k "test_user"           # Tests matching pattern
poetry run pytest --lf                     # Last failed tests only

# Code Quality
poetry run black .                         # Format code
poetry run black --check .                 # Check formatting
poetry run ruff check .                    # Lint
poetry run ruff check --fix .              # Lint and fix
poetry run mypy src/                       # Type check

# Database
poetry run alembic revision --autogenerate -m "message"  # Create migration
poetry run alembic upgrade head                           # Apply migrations
poetry run alembic downgrade -1                           # Rollback one
poetry run alembic current                                # Show current
poetry run alembic history                                # Show history

# Dependencies
poetry add [package]                       # Add package
poetry add --group dev [package]           # Add dev package
poetry update                              # Update all packages
poetry show                                # List installed packages
poetry show [package]                      # Show package details
```

### **Frontend Commands**

```bash
# Development
npm run dev                               # Start dev server
npm run dev -- --host 0.0.0.0            # Accessible from network

# Testing
npm test                                  # Run tests
npm run test:ui                           # Run tests with UI
npm run test -- --coverage                # With coverage

# Code Quality
npm run lint                              # Lint
npm run format                            # Format code
npm run check                             # Type check

# Build
npm run build                             # Build for production
npm run preview                           # Preview production build
```

### **Docker Commands**

```bash
# Start/Stop
docker-compose up -d                      # Start all services
docker-compose down                       # Stop all services
docker-compose down -v                    # Stop and remove volumes
docker-compose restart [service]          # Restart specific service

# Logs
docker-compose logs -f                    # Follow all logs
docker-compose logs -f backend            # Follow backend logs
docker-compose logs --tail=100 backend    # Last 100 lines

# Execute Commands
docker-compose exec backend bash          # Backend shell
docker-compose exec postgres psql -U shinkei_user -d shinkei  # Database shell
docker-compose exec backend poetry run pytest  # Run tests in container

# Rebuild
docker-compose build                      # Rebuild all
docker-compose build --no-cache backend   # Rebuild backend without cache

# Clean Up
docker-compose down --rmi all --volumes   # Remove everything
docker system prune -a                    # Clean Docker system
```

### **Git Commands**

```bash
# Branch Management
git checkout -b feature/new-feature       # Create and switch to branch
git branch -d feature/old-feature         # Delete local branch
git push origin --delete feature/old      # Delete remote branch

# Committing
git add .                                 # Stage all changes
git commit -m "feat: message"             # Commit with message
git commit --amend                        # Amend last commit

# Syncing
git fetch origin                          # Fetch remote changes
git pull origin develop                   # Pull from develop
git push origin feature/branch            # Push branch

# Merging
git merge develop                         # Merge develop into current
git rebase develop                        # Rebase onto develop

# Stashing
git stash                                 # Stash changes
git stash pop                             # Apply and remove stash
git stash list                            # List stashes

# History
git log --oneline --graph --all          # Visual history
git log --author="name"                   # Commits by author
git show [commit-hash]                    # Show commit details
```

---

## **PART VIII: TROUBLESHOOTING QUICK FIXES**

### **"Port already in use"**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 [PID]

# Or use different port
uvicorn src.shinkei.main:app --port 8001
```

### **"Module not found"**
```bash
# Reinstall dependencies
poetry install

# Clear cache
find . -type d -name __pycache__ -exec rm -r {} +

# Check Python path
poetry run python -c "import sys; print(sys.path)"
```

### **"Database connection refused"**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check connection string
echo $DATABASE_URL

# Restart database
docker-compose restart postgres
```

### **"Migration conflict"**
```bash
# Check current state
poetry run alembic current

# Rollback
poetry run alembic downgrade -1

# Delete conflicting migration file
rm alembic/versions/[conflict].py

# Regenerate
poetry run alembic revision --autogenerate -m "new migration"
```

### **"Tests hanging or timing out"**
```bash
# Run with timeout
poetry run pytest --timeout=10

# Check for infinite loops in async code

# Check for missing await keywords

# Check database connections are closed
```

---

## **PART IX: CODE REVIEW CHECKLIST**

Before committing, verify:

### **Code Quality**
- [ ] Code follows project style guide
- [ ] No commented-out code
- [ ] No debugging print statements
- [ ] No hardcoded values (use config)
- [ ] Meaningful variable/function names
- [ ] Functions are small and focused
- [ ] No code duplication

### **Testing**
- [ ] Unit tests written and passing
- [ ] Integration tests written (if applicable)
- [ ] Test coverage ≥ 80%
- [ ] Edge cases tested
- [ ] Error cases tested

### **Security**
- [ ] No secrets in code
- [ ] Input validation implemented
- [ ] Authorization checks in place
- [ ] SQL injection prevented (use ORM)
- [ ] XSS prevented (frontend)
- [ ] CSRF protection (if needed)

### **Performance**
- [ ] No N+1 queries
- [ ] Appropriate indexes added
- [ ] Pagination implemented
- [ ] Async/await used properly

### **Documentation**
- [ ] Docstrings added
- [ ] Complex logic commented
- [ ] API documentation updated
- [ ] README updated (if needed)

---

## **PART X: RESOURCES AND REFERENCES**

### **Quick Links**

- **Backend API Docs**: http://localhost:8000/docs
- **Frontend Dev**: http://localhost:5173
- **Database**: postgresql://shinkei_user:shinkei_pass@localhost:5432/shinkei

### **Documentation**

- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/en/20/
- Pydantic: https://docs.pydantic.dev/
- Alembic: https://alembic.sqlalchemy.org/
- Pytest: https://docs.pytest.org/
- SvelteKit: https://kit.svelte.dev/docs

### **Community**

- GitHub Issues: Report bugs and feature requests
- Discord: [Project Discord Link]
- Wiki: Internal documentation

---

**Remember**: When in doubt, write a test first, then implement the feature. This ensures your code works and prevents regressions.

**Happy Coding! 🚀**

