# 🚀 **SHINKEI (心継) - COMPREHENSIVE IMPLEMENTATION PLAN**

## **Version:** 1.0.0  
## **Target Audience:** Claude Code + Development Team  
## **Methodology:** Iterative, Test-Driven, Secure-by-Design

---

# **TABLE OF CONTENTS**

1. [Project Foundation & Setup](#phase-0)
2. [Database Layer & Core Models](#phase-1)
3. [Authentication & Security](#phase-2)
4. [Core CRUD Operations](#phase-3)
5. [AI Engine Foundation](#phase-4)
6. [Narrative Generation Pipeline](#phase-5)
7. [Frontend Foundation](#phase-6)
8. [World & Timeline Management](#phase-7)
9. [Story Management](#phase-8)
10. [Multi-Mode Authoring System](#phase-9)
11. [Cross-Story Intersections](#phase-10)
12. [GraphRAG Preparation](#phase-11)
13. [Production Readiness](#phase-12)

---

# **IMPLEMENTATION PRINCIPLES**

## **Core Principles**
1. **Test-First Development**: Every feature must have tests before implementation
2. **Security at Every Layer**: Authentication, authorization, input validation
3. **Incremental Delivery**: Each step produces a working, testable artifact
4. **Documentation Inline**: Code documentation as you build
5. **No Breaking Changes**: Schema evolution, not revolution

## **Testing Strategy**
- **Unit Tests**: 80%+ coverage minimum per module
- **Integration Tests**: API endpoint testing with real database
- **E2E Tests**: Critical user journeys
- **Security Tests**: OWASP Top 10 validation per phase

## **Quality Gates**
Each phase must pass:
1. ✅ All unit tests passing
2. ✅ Integration tests passing
3. ✅ Security scan clean
4. ✅ Code review checklist complete
5. ✅ Documentation updated

---

# **PHASE 0: PROJECT FOUNDATION & SETUP**

## **Duration**: 3-5 days
## **Goal**: Establish development environment, tooling, and project structure

---

### **MILESTONE 0.1: Repository & Project Structure**

#### **Deliverables**
```
shinkei/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── security-scan.yml
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── src/
│   │   └── shinkei/
│   │       ├── __init__.py
│   │       ├── config.py
│   │       └── main.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── unit/
│   ├── pyproject.toml
│   ├── poetry.lock
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   ├── routes/
│   │   └── app.html
│   ├── static/
│   ├── tests/
│   ├── package.json
│   ├── svelte.config.js
│   └── README.md
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docs/
│   ├── architecture/
│   ├── api/
│   └── development/
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

#### **Step-by-Step Instructions**

**Step 0.1.1: Initialize Git Repository**
```bash
# Create project structure
mkdir -p shinkei/{backend,frontend,docker,docs}
cd shinkei
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# Node
node_modules/
.svelte-kit/
build/
.DS_Store

# Environment
.env
.env.local
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
*.db
*.sqlite

# Test coverage
.coverage
htmlcov/
.pytest_cache/

# OS
.DS_Store
Thumbs.db
EOF
```

**Step 0.1.2: Backend Foundation (Python/FastAPI)**
```bash
cd backend

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "shinkei-backend"
version = "0.1.0"
description = "Shinkei Narrative Engine - Backend API"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.32.0"}
pydantic = "^2.9.0"
pydantic-settings = "^2.6.0"
sqlalchemy = "^2.0.35"
alembic = "^1.13.3"
psycopg2-binary = "^2.9.10"
asyncpg = "^0.30.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.17"
httpx = "^0.28.0"
supabase = "^2.9.1"
opentelemetry-api = "^1.28.2"
opentelemetry-sdk = "^1.28.2"
opentelemetry-instrumentation-fastapi = "^0.49b2"
structlog = "^24.4.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.3"
pytest-asyncio = "^0.24.0"
pytest-cov = "^6.0.0"
pytest-mock = "^3.14.0"
black = "^24.10.0"
ruff = "^0.7.4"
mypy = "^1.13.0"
httpx = "^0.28.0"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=src --cov-report=html --cov-report=term"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

# Install dependencies
poetry install
```

**Step 0.1.3: Frontend Foundation (SvelteKit)**
```bash
cd ../frontend

# Initialize SvelteKit project
npm create svelte@latest . -- --template skeleton --types typescript

# Install additional dependencies
npm install -D @sveltejs/adapter-node
npm install @supabase/supabase-js
npm install @supabase/auth-helpers-sveltekit

# Create package.json scripts
cat > package.json << 'EOF'
{
  "name": "shinkei-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
    "check:watch": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --watch",
    "lint": "prettier --check . && eslint .",
    "format": "prettier --write ."
  },
  "devDependencies": {
    "@sveltejs/adapter-node": "^5.2.9",
    "@sveltejs/kit": "^2.7.7",
    "@sveltejs/vite-plugin-svelte": "^4.0.1",
    "svelte": "^5.2.9",
    "svelte-check": "^4.0.8",
    "typescript": "^5.7.2",
    "vite": "^6.0.1",
    "vitest": "^2.1.6",
    "@testing-library/svelte": "^5.2.4",
    "jsdom": "^25.0.1",
    "prettier": "^3.3.3",
    "prettier-plugin-svelte": "^3.2.8",
    "eslint": "^9.15.0",
    "eslint-plugin-svelte": "^2.46.1"
  },
  "dependencies": {
    "@supabase/supabase-js": "^2.46.2",
    "@supabase/auth-helpers-sveltekit": "^0.13.0"
  },
  "type": "module"
}
EOF

npm install
```

**Step 0.1.4: Docker Compose Setup**
```bash
cd ../docker

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL database
  postgres:
    image: postgres:16-alpine
    container_name: shinkei-postgres
    environment:
      POSTGRES_DB: shinkei
      POSTGRES_USER: shinkei_user
      POSTGRES_PASSWORD: shinkei_pass_dev_only
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shinkei_user -d shinkei"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Supabase local stack (will add in Phase 2)
  
  # Backend API
  backend:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
    container_name: shinkei-backend
    environment:
      DATABASE_URL: postgresql://shinkei_user:shinkei_pass_dev_only@postgres:5432/shinkei
      ENVIRONMENT: development
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ../backend:/app
    command: uvicorn src.shinkei.main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend
  frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.frontend
    container_name: shinkei-frontend
    environment:
      PUBLIC_API_URL: http://localhost:8000
    ports:
      - "5173:5173"
    depends_on:
      - backend
    volumes:
      - ../frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0

volumes:
  postgres_data:
EOF

# Backend Dockerfile
cat > Dockerfile.backend << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.shinkei.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Frontend Dockerfile
cat > Dockerfile.frontend << 'EOF'
FROM node:20-alpine

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
EOF
```

#### **Testing Checklist**
- [ ] Repository initializes successfully
- [ ] Python dependencies install without errors
- [ ] Node dependencies install without errors
- [ ] Docker Compose builds all services
- [ ] PostgreSQL starts and accepts connections
- [ ] Backend API responds to health check
- [ ] Frontend development server starts

#### **Unit Tests**

**Test File: `backend/tests/test_setup.py`**
```python
"""Test basic project setup and configuration."""
import pytest
from src.shinkei import __version__


def test_version():
    """Test package version is defined."""
    assert __version__ is not None


def test_imports():
    """Test core imports work."""
    try:
        from src.shinkei.config import settings
        from src.shinkei.main import app
        assert settings is not None
        assert app is not None
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")
```

**Run Tests:**
```bash
cd backend
poetry run pytest
```

---

### **MILESTONE 0.2: Configuration Management**

#### **Deliverables**
- Environment-based configuration system
- Secrets management structure
- Logging infrastructure

#### **Step-by-Step Instructions**

**Step 0.2.1: Backend Configuration (`backend/src/shinkei/config.py`)**
```python
"""Application configuration management."""
from typing import Literal
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    
    # Application
    app_name: str = "Shinkei"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    
    # Database
    database_url: PostgresDsn = Field(
        default="postgresql://shinkei_user:shinkei_pass@localhost:5432/shinkei"
    )
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    
    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT encoding"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Supabase
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")
    supabase_jwt_secret: str = Field(default="")
    
    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )
    
    # AI/LLM
    default_llm_provider: str = "openai"
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    
    # Observability
    enable_telemetry: bool = False
    otel_endpoint: str = Field(default="")
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000


settings = Settings()
```

**Step 0.2.2: Environment Files**

Create `.env.example`:
```bash
cat > backend/.env.example << 'EOF'
# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://shinkei_user:shinkei_pass@localhost:5432/shinkei

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your-secret-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# AI/LLM (optional for local development)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Observability (optional)
ENABLE_TELEMETRY=false
OTEL_ENDPOINT=
EOF
```

**Step 0.2.3: Logging Setup (`backend/src/shinkei/logging_config.py`)**
```python
"""Structured logging configuration."""
import logging
import structlog
from src.shinkei.config import settings


def configure_logging() -> None:
    """Configure structured logging with structlog."""
    
    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG if settings.debug else logging.INFO,
    )
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.environment == "development":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)
```

#### **Unit Tests**

**Test File: `backend/tests/unit/test_config.py`**
```python
"""Test configuration management."""
import pytest
from pydantic import ValidationError
from src.shinkei.config import Settings


def test_settings_default_values():
    """Test default configuration values."""
    settings = Settings()
    assert settings.environment == "development"
    assert settings.app_name == "Shinkei"
    assert settings.debug is False


def test_settings_from_env(monkeypatch):
    """Test configuration from environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "true")
    
    settings = Settings()
    assert settings.environment == "production"
    assert settings.debug is True


def test_database_url_validation():
    """Test database URL must be valid PostgreSQL DSN."""
    with pytest.raises(ValidationError):
        Settings(database_url="invalid-url")


def test_required_security_settings():
    """Test security settings are present."""
    settings = Settings()
    assert settings.secret_key is not None
    assert len(settings.secret_key) > 0
```

**Test File: `backend/tests/unit/test_logging.py`**
```python
"""Test logging configuration."""
import structlog
from src.shinkei.logging_config import configure_logging, get_logger


def test_logging_configuration():
    """Test logging is properly configured."""
    configure_logging()
    logger = get_logger("test")
    
    assert isinstance(logger, structlog.BoundLogger)
    logger.info("test_message", test_key="test_value")


def test_get_logger_returns_bound_logger():
    """Test get_logger returns proper logger type."""
    configure_logging()
    logger = get_logger("test.module")
    
    assert isinstance(logger, structlog.BoundLogger)
    assert logger._context == {}
```

---

### **MILESTONE 0.3: Database Connection & Health Checks**

#### **Deliverables**
- SQLAlchemy async engine setup
- Database connection management
- Health check endpoints
- Alembic migration infrastructure

#### **Step-by-Step Instructions**

**Step 0.3.1: Database Engine (`backend/src/shinkei/database/engine.py`)**
```python
"""Database engine and session management."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from src.shinkei.config import settings
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Create async engine
engine = create_async_engine(
    str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables (for development only)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("database_connections_closed")
```

**Step 0.3.2: Alembic Setup**
```bash
cd backend
poetry run alembic init alembic

# Edit alembic.ini
cat > alembic.ini << 'EOF'
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[alembic:exclude]
tables = spatial_ref_sys

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF
```

**Edit `alembic/env.py`:**
```python
"""Alembic environment configuration."""
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import the base and models
from src.shinkei.database.engine import Base
from src.shinkei.config import settings

# Alembic Config object
config = context.config

# Override database URL from settings
config.set_main_option(
    "sqlalchemy.url",
    str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://")
)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 0.3.3: FastAPI Application (`backend/src/shinkei/main.py`)**
```python
"""Main FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.shinkei.config import settings
from src.shinkei.database.engine import close_db, init_db
from src.shinkei.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    configure_logging()
    logger.info("application_starting", environment=settings.environment)
    
    if settings.environment == "development":
        await init_db()
    
    yield
    
    # Shutdown
    await close_db()
    logger.info("application_shutdown_complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> JSONResponse:
    """
    Health check endpoint.
    
    Returns:
        JSONResponse: Application health status
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.environment,
            "version": settings.app_version,
        }
    )


@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> JSONResponse:
    """
    Root endpoint.
    
    Returns:
        JSONResponse: Welcome message
    """
    return JSONResponse(
        content={
            "message": f"Welcome to {settings.app_name} API",
            "version": settings.app_version,
            "docs": "/docs",
        }
    )
```

#### **Unit Tests**

**Test File: `backend/tests/unit/test_database.py`**
```python
"""Test database connection and session management."""
import pytest
from sqlalchemy import text
from src.shinkei.database.engine import get_db, init_db, close_db, Base


@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection can be established."""
    async for session in get_db():
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_database_session_rollback():
    """Test database session rolls back on error."""
    with pytest.raises(Exception):
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            raise Exception("Test error")


@pytest.mark.asyncio
async def test_init_db_creates_tables():
    """Test database initialization creates tables."""
    await init_db()
    # Tables will be verified when models are added
    assert True


@pytest.mark.asyncio
async def test_close_db():
    """Test database connections can be closed."""
    await close_db()
    assert True
```

**Test File: `backend/tests/integration/test_api_health.py`**
```python
"""Integration tests for health check endpoints."""
import pytest
from httpx import AsyncClient
from src.shinkei.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint returns 200."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint returns welcome message."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
```

#### **Testing Checklist**
- [ ] Database engine initializes successfully
- [ ] Database sessions can be created and committed
- [ ] Database sessions roll back on errors
- [ ] Health check endpoint returns 200
- [ ] Alembic can generate migrations
- [ ] All unit tests pass
- [ ] All integration tests pass

---

### **MILESTONE 0.4: CI/CD Pipeline**

#### **Deliverables**
- GitHub Actions workflow for testing
- Code quality checks (linting, type checking)
- Security scanning

#### **Step-by-Step Instructions**

**Step 0.4.1: GitHub Actions CI (``.github/workflows/ci.yml`)**
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: shinkei_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        working-directory: ./backend
        run: |
          poetry install --no-interaction
      
      - name: Run linting
        working-directory: ./backend
        run: |
          poetry run black --check .
          poetry run ruff check .
      
      - name: Run type checking
        working-directory: ./backend
        run: |
          poetry run mypy src/
      
      - name: Run tests
        working-directory: ./backend
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/shinkei_test
        run: |
          poetry run pytest --cov --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./backend/coverage.xml
          fail_ci_if_error: false

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: './frontend/package-lock.json'
      
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Run linting
        working-directory: ./frontend
        run: npm run lint
      
      - name: Run type checking
        working-directory: ./frontend
        run: npm run check
      
      - name: Run tests
        working-directory: ./frontend
        run: npm test
```

**Step 0.4.2: Security Scanning (`.github/workflows/security-scan.yml`)**
```yaml
name: Security Scan

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

---

## **PHASE 0 COMPLETION CHECKLIST**

### **Deliverables Verification**
- [ ] Repository structure complete
- [ ] Backend dependencies installed and working
- [ ] Frontend dependencies installed and working
- [ ] Docker Compose setup functional
- [ ] Configuration management implemented
- [ ] Logging infrastructure in place
- [ ] Database connection established
- [ ] Health check endpoints working
- [ ] Alembic migration system ready
- [ ] CI/CD pipeline configured and passing
- [ ] All unit tests passing (minimum 80% coverage)
- [ ] All integration tests passing
- [ ] Documentation updated

### **Security Checklist**
- [ ] No secrets in repository
- [ ] `.env.example` provided
- [ ] `.gitignore` properly configured
- [ ] Security scanning configured
- [ ] CORS properly configured

### **Quality Gates**
- [ ] Code formatted with Black
- [ ] Linting passes (Ruff)
- [ ] Type checking passes (mypy)
- [ ] Test coverage ≥ 80%
- [ ] All tests passing

---

# **PHASE 1: DATABASE LAYER & CORE MODELS**

## **Duration**: 5-7 days
## **Goal**: Implement complete database schema with migrations and repository pattern

---

### **MILESTONE 1.1: User Model & Repository**

#### **Deliverables**
- User SQLAlchemy model
- User repository with CRUD operations
- Alembic migration for users table
- Comprehensive unit tests

#### **Step-by-Step Instructions**

**Step 1.1.1: User Model (`backend/src/shinkei/models/user.py`)**
```python
"""User model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.shinkei.database.engine import Base
import uuid


class User(Base):
    """
    User model representing a Shinkei author.
    
    Attributes:
        id: Unique identifier (UUID from Supabase Auth)
        email: User email address
        name: Display name
        settings: JSON object containing user preferences
        created_at: Timestamp of user creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="UUID from Supabase Auth"
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address"
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name"
    )
    
    settings: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="User preferences (language, theme, default_model, etc.)"
    )
    
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
    
    # Relationships (will be added as we build other models)
    # worlds: Mapped[list["World"]] = relationship(back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
```

**Step 1.1.2: User Schema (`backend/src/shinkei/schemas/user.py`)**
```python
"""User Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserSettings(BaseModel):
    """User settings schema."""
    language: str = "en"
    default_model: str = "gpt-4"
    ui_theme: str = "system"  # "light", "dark", "system"


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    settings: UserSettings = Field(default_factory=UserSettings)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    id: Optional[str] = None  # Will be provided by Supabase Auth


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    model_config = ConfigDict(extra='forbid')
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    settings: Optional[UserSettings] = None


class UserResponse(UserBase):
    """Schema for user responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
```

**Step 1.1.3: User Repository (`backend/src/shinkei/repositories/user.py`)**
```python
"""User repository for database operations."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.models.user import User
from src.shinkei.schemas.user import UserCreate, UserUpdate
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Repository for User model database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user instance
        """
        user = User(
            id=user_data.id,
            email=user_data.email,
            name=user_data.name,
            settings=user_data.settings.model_dump(),
        )
        
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        
        logger.info("user_created", user_id=user.id, email=user.email)
        return user
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def update(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User UUID
            user_data: Update data
            
        Returns:
            Updated user instance or None if not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        if "name" in update_data:
            user.name = update_data["name"]
        
        if "settings" in update_data:
            user.settings = update_data["settings"]
        
        await self.session.flush()
        await self.session.refresh(user)
        
        logger.info("user_updated", user_id=user.id)
        return user
    
    async def delete(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if deleted, False if not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        await self.session.delete(user)
        await self.session.flush()
        
        logger.info("user_deleted", user_id=user_id)
        return True
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[User], int]:
        """
        List users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (users list, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(func.count()).select_from(User)
        )
        total = count_result.scalar_one()
        
        # Get users
        result = await self.session.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        users = list(result.scalars().all())
        
        return users, total
    
    async def exists(self, user_id: str) -> bool:
        """
        Check if user exists.
        
        Args:
            user_id: User UUID
            
        Returns:
            True if user exists, False otherwise
        """
        result = await self.session.execute(
            select(func.count()).select_from(User).where(User.id == user_id)
        )
        return result.scalar_one() > 0
```

**Step 1.1.4: Create Migration**
```bash
cd backend
poetry run alembic revision --autogenerate -m "create_users_table"
poetry run alembic upgrade head
```

#### **Unit Tests**

**Test File: `backend/tests/unit/test_models_user.py`**
```python
"""Unit tests for User model."""
import pytest
from src.shinkei.models.user import User


def test_user_model_creation():
    """Test User model can be instantiated."""
    user = User(
        id="test-uuid",
        email="test@example.com",
        name="Test User",
        settings={"language": "en"}
    )
    
    assert user.id == "test-uuid"
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.settings == {"language": "en"}


def test_user_model_repr():
    """Test User model string representation."""
    user = User(
        id="test-uuid",
        email="test@example.com",
        name="Test User"
    )
    
    repr_str = repr(user)
    assert "test-uuid" in repr_str
    assert "test@example.com" in repr_str
```

**Test File: `backend/tests/unit/test_schemas_user.py`**
```python
"""Unit tests for User schemas."""
import pytest
from pydantic import ValidationError
from src.shinkei.schemas.user import (
    UserSettings,
    UserCreate,
    UserUpdate,
    UserResponse
)


def test_user_settings_defaults():
    """Test UserSettings has correct defaults."""
    settings = UserSettings()
    assert settings.language == "en"
    assert settings.default_model == "gpt-4"
    assert settings.ui_theme == "system"


def test_user_create_valid():
    """Test UserCreate with valid data."""
    user_data = UserCreate(
        email="test@example.com",
        name="Test User"
    )
    assert user_data.email == "test@example.com"
    assert user_data.name == "Test User"


def test_user_create_invalid_email():
    """Test UserCreate rejects invalid email."""
    with pytest.raises(ValidationError):
        UserCreate(email="invalid-email", name="Test User")


def test_user_update_partial():
    """Test UserUpdate allows partial updates."""
    update = UserUpdate(name="New Name")
    assert update.name == "New Name"
    assert update.settings is None


def test_user_update_forbids_extra_fields():
    """Test UserUpdate rejects extra fields."""
    with pytest.raises(ValidationError):
        UserUpdate(name="Test", extra_field="not allowed")
```

**Test File: `backend/tests/integration/test_repository_user.py`**
```python
"""Integration tests for User repository."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.repositories.user import UserRepository
from src.shinkei.schemas.user import UserCreate, UserUpdate, UserSettings


@pytest.fixture
async def user_repo(db_session: AsyncSession) -> UserRepository:
    """Create UserRepository instance."""
    return UserRepository(db_session)


@pytest.fixture
async def sample_user_data() -> UserCreate:
    """Sample user creation data."""
    return UserCreate(
        id="test-user-id",
        email="test@example.com",
        name="Test User",
        settings=UserSettings()
    )


@pytest.mark.asyncio
async def test_create_user(user_repo: UserRepository, sample_user_data: UserCreate):
    """Test creating a new user."""
    user = await user_repo.create(sample_user_data)
    
    assert user.id == sample_user_data.id
    assert user.email == sample_user_data.email
    assert user.name == sample_user_data.name
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_get_user_by_id(user_repo: UserRepository, sample_user_data: UserCreate):
    """Test retrieving user by ID."""
    created_user = await user_repo.create(sample_user_data)
    retrieved_user = await user_repo.get_by_id(created_user.id)
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id


@pytest.mark.asyncio
async def test_get_user_by_email(user_repo: UserRepository, sample_user_data: UserCreate):
    """Test retrieving user by email."""
    created_user = await user_repo.create(sample_user_data)
    retrieved_user = await user_repo.get_by_email(created_user.email)
    
    assert retrieved_user is not None
    assert retrieved_user.email == created_user.email


@pytest.mark.asyncio
async def test_update_user(user_repo: UserRepository, sample_user_data: UserCreate):
    """Test updating user information."""
    created_user = await user_repo.create(sample_user_data)
    
    update_data = UserUpdate(name="Updated Name")
    updated_user = await user_repo.update(created_user.id, update_data)
    
    assert updated_user is not None
    assert updated_user.name == "Updated Name"


@pytest.mark.asyncio
async def test_delete_user(user_repo: UserRepository, sample_user_data: UserCreate):
    """Test deleting a user."""
    created_user = await user_repo.create(sample_user_data)
    
    deleted = await user_repo.delete(created_user.id)
    assert deleted is True
    
    retrieved_user = await user_repo.get_by_id(created_user.id)
    assert retrieved_user is None


@pytest.mark.asyncio
async def test_list_users(user_repo: UserRepository):
    """Test listing users with pagination."""
    # Create multiple users
    for i in range(5):
        await user_repo.create(
            UserCreate(
                id=f"user-{i}",
                email=f"user{i}@example.com",
                name=f"User {i}"
            )
        )
    
    users, total = await user_repo.list_users(skip=0, limit=10)
    
    assert total == 5
    assert len(users) == 5


@pytest.mark.asyncio
async def test_user_exists(user_repo: UserRepository, sample_user_data: UserCreate):
    """Test checking if user exists."""
    created_user = await user_repo.create(sample_user_data)
    
    exists = await user_repo.exists(created_user.id)
    assert exists is True
    
    exists = await user_repo.exists("non-existent-id")
    assert exists is False
```

**Pytest Configuration (`backend/tests/conftest.py`)**
```python
"""Pytest configuration and fixtures."""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.shinkei.database.engine import Base
from src.shinkei.config import settings


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Get test database URL."""
    return str(settings.database_url).replace("shinkei", "shinkei_test")


@pytest_asyncio.fixture(scope="function")
async def db_session(test_database_url: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for tests.
    Each test gets a fresh session with tables created/dropped.
    """
    engine = create_async_engine(
        test_database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        finally:
            await session.rollback()
    
    # Cleanup
    await engine.dispose()
```

---

### **MILESTONE 1.2: World Model & Repository**

#### **Deliverables**
- World SQLAlchemy model with JSON fields for laws and settings
- World repository with CRUD operations
- Migration for worlds table with foreign key to users
- Comprehensive unit and integration tests

#### **Step-by-Step Instructions**

**Step 1.2.1: World Model (`backend/src/shinkei/models/world.py`)**
```python
"""World model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, JSON, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.shinkei.database.engine import Base
import uuid
import enum


class ChronologyMode(str, enum.Enum):
    """Chronology mode enumeration."""
    LINEAR = "linear"
    FRAGMENTED = "fragmented"
    TIMELESS = "timeless"


class World(Base):
    """
    World model representing a narrative universe.
    
    Attributes:
        id: Unique identifier
        user_id: Foreign key to user who created the world
        name: World name
        description: General pitch/summary
        tone: Narrative tone (e.g., "calm, introspective, cold")
        backdrop: World bible, overarching lore
        laws: JSON object containing world rules (physics, metaphysics, social, forbidden)
        chronology_mode: How time flows in this world
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "worlds"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="World UUID"
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="World name"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="General pitch/summary"
    )
    
    tone: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Narrative tone"
    )
    
    backdrop: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="World bible, overarching lore"
    )
    
    laws: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="World rules (physics, metaphysics, social, forbidden)"
    )
    
    chronology_mode: Mapped[ChronologyMode] = mapped_column(
        SQLEnum(ChronologyMode),
        nullable=False,
        default=ChronologyMode.LINEAR,
        comment="How time flows in this world"
    )
    
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
    user: Mapped["User"] = relationship("User", back_populates="worlds")
    # world_events: Mapped[list["WorldEvent"]] = relationship(back_populates="world")
    # stories: Mapped[list["Story"]] = relationship(back_populates="world")
    
    def __repr__(self) -> str:
        return f"<World(id={self.id}, name={self.name}, user_id={self.user_id})>"
```

**Update User Model to add relationship (`backend/src/shinkei/models/user.py`)**
```python
# Add this import at the top
from sqlalchemy.orm import relationship

# Add this relationship inside the User class
worlds: Mapped[list["World"]] = relationship("World", back_populates="user", cascade="all, delete-orphan")
```

**Step 1.2.2: World Schema (`backend/src/shinkei/schemas/world.py`)**
```python
"""World Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class WorldLaws(BaseModel):
    """World laws schema."""
    physics: Optional[str] = None
    metaphysics: Optional[str] = None
    social: Optional[str] = None
    forbidden: Optional[str] = None


class WorldBase(BaseModel):
    """Base world schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tone: Optional[str] = Field(None, max_length=500)
    backdrop: Optional[str] = None
    laws: WorldLaws = Field(default_factory=WorldLaws)
    chronology_mode: str = Field(default="linear", pattern="^(linear|fragmented|timeless)$")


class WorldCreate(WorldBase):
    """Schema for creating a new world."""
    pass


class WorldUpdate(BaseModel):
    """Schema for updating a world."""
    model_config = ConfigDict(extra='forbid')
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tone: Optional[str] = Field(None, max_length=500)
    backdrop: Optional[str] = None
    laws: Optional[WorldLaws] = None
    chronology_mode: Optional[str] = Field(None, pattern="^(linear|fragmented|timeless)$")


class WorldResponse(WorldBase):
    """Schema for world responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class WorldListResponse(BaseModel):
    """Schema for paginated world list."""
    worlds: list[WorldResponse]
    total: int
    page: int
    page_size: int
```

**Step 1.2.3: World Repository (`backend/src/shinkei/repositories/world.py`)**
```python
"""World repository for database operations."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.models.world import World, ChronologyMode
from src.shinkei.schemas.world import WorldCreate, WorldUpdate
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


class WorldRepository:
    """Repository for World model database operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(self, user_id: str, world_data: WorldCreate) -> World:
        """
        Create a new world.
        
        Args:
            user_id: Owner user ID
            world_data: World creation data
            
        Returns:
            Created world instance
        """
        world = World(
            user_id=user_id,
            name=world_data.name,
            description=world_data.description,
            tone=world_data.tone,
            backdrop=world_data.backdrop,
            laws=world_data.laws.model_dump(),
            chronology_mode=ChronologyMode(world_data.chronology_mode),
        )
        
        self.session.add(world)
        await self.session.flush()
        await self.session.refresh(world)
        
        logger.info("world_created", world_id=world.id, user_id=user_id)
        return world
    
    async def get_by_id(self, world_id: str) -> Optional[World]:
        """
        Get world by ID.
        
        Args:
            world_id: World UUID
            
        Returns:
            World instance or None if not found
        """
        result = await self.session.execute(
            select(World).where(World.id == world_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_and_id(self, user_id: str, world_id: str) -> Optional[World]:
        """
        Get world by user ID and world ID.
        
        Args:
            user_id: User UUID
            world_id: World UUID
            
        Returns:
            World instance or None if not found or not owned by user
        """
        result = await self.session.execute(
            select(World).where(
                World.id == world_id,
                World.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[World], int]:
        """
        List worlds owned by a specific user.
        
        Args:
            user_id: User UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (worlds list, total count)
        """
        # Get total count
        count_result = await self.session.execute(
            select(func.count())
            .select_from(World)
            .where(World.user_id == user_id)
        )
        total = count_result.scalar_one()
        
        # Get worlds
        result = await self.session.execute(
            select(World)
            .where(World.user_id == user_id)
            .order_by(World.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        worlds = list(result.scalars().all())
        
        return worlds, total
    
    async def update(
        self,
        world_id: str,
        world_data: WorldUpdate
    ) -> Optional[World]:
        """
        Update world information.
        
        Args:
            world_id: World UUID
            world_data: Update data
            
        Returns:
            Updated world instance or None if not found
        """
        world = await self.get_by_id(world_id)
        if not world:
            return None
        
        update_data = world_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "laws" and value is not None:
                setattr(world, field, value)
            elif field == "chronology_mode" and value is not None:
                setattr(world, field, ChronologyMode(value))
            elif value is not None:
                setattr(world, field, value)
        
        await self.session.flush()
        await self.session.refresh(world)
        
        logger.info("world_updated", world_id=world.id)
        return world
    
    async def delete(self, world_id: str) -> bool:
        """
        Delete a world.
        
        Args:
            world_id: World UUID
            
        Returns:
            True if deleted, False if not found
        """
        world = await self.get_by_id(world_id)
        if not world:
            return False
        
        await self.session.delete(world)
        await self.session.flush()
        
        logger.info("world_deleted", world_id=world_id)
        return True
    
    async def exists(self, world_id: str) -> bool:
        """
        Check if world exists.
        
        Args:
            world_id: World UUID
            
        Returns:
            True if world exists, False otherwise
        """
        result = await self.session.execute(
            select(func.count()).select_from(World).where(World.id == world_id)
        )
        return result.scalar_one() > 0
```

**Step 1.2.4: Create Migration**
```bash
cd backend
poetry run alembic revision --autogenerate -m "create_worlds_table"
poetry run alembic upgrade head
```

#### **Unit Tests**

**Test File: `backend/tests/integration/test_repository_world.py`**
```python
"""Integration tests for World repository."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.repositories.user import UserRepository
from src.shinkei.repositories.world import WorldRepository
from src.shinkei.schemas.user import UserCreate
from src.shinkei.schemas.world import WorldCreate, WorldUpdate, WorldLaws


@pytest.fixture
async def user_repo(db_session: AsyncSession) -> UserRepository:
    """Create UserRepository instance."""
    return UserRepository(db_session)


@pytest.fixture
async def world_repo(db_session: AsyncSession) -> WorldRepository:
    """Create WorldRepository instance."""
    return WorldRepository(db_session)


@pytest.fixture
async def test_user(user_repo: UserRepository) -> str:
    """Create a test user and return their ID."""
    user = await user_repo.create(
        UserCreate(
            id="test-user-id",
            email="test@example.com",
            name="Test User"
        )
    )
    return user.id


@pytest.fixture
async def sample_world_data() -> WorldCreate:
    """Sample world creation data."""
    return WorldCreate(
        name="Test World",
        description="A test narrative universe",
        tone="mysterious, contemplative",
        backdrop="A world where reality bends",
        laws=WorldLaws(
            physics="Gravity works normally",
            metaphysics="Dreams can become real",
            social="Community is paramount",
            forbidden="No time travel"
        ),
        chronology_mode="linear"
    )


@pytest.mark.asyncio
async def test_create_world(
    world_repo: WorldRepository,
    test_user: str,
    sample_world_data: WorldCreate
):
    """Test creating a new world."""
    world = await world_repo.create(test_user, sample_world_data)
    
    assert world.id is not None
    assert world.user_id == test_user
    assert world.name == sample_world_data.name
    assert world.created_at is not None


@pytest.mark.asyncio
async def test_get_world_by_id(
    world_repo: WorldRepository,
    test_user: str,
    sample_world_data: WorldCreate
):
    """Test retrieving world by ID."""
    created_world = await world_repo.create(test_user, sample_world_data)
    retrieved_world = await world_repo.get_by_id(created_world.id)
    
    assert retrieved_world is not None
    assert retrieved_world.id == created_world.id


@pytest.mark.asyncio
async def test_get_world_by_user_and_id(
    world_repo: WorldRepository,
    test_user: str,
    sample_world_data: WorldCreate
):
    """Test retrieving world by user ID and world ID."""
    created_world = await world_repo.create(test_user, sample_world_data)
    retrieved_world = await world_repo.get_by_user_and_id(test_user, created_world.id)
    
    assert retrieved_world is not None
    assert retrieved_world.user_id == test_user


@pytest.mark.asyncio
async def test_list_worlds_by_user(
    world_repo: WorldRepository,
    test_user: str
):
    """Test listing worlds for a specific user."""
    # Create multiple worlds
    for i in range(3):
        await world_repo.create(
            test_user,
            WorldCreate(
                name=f"World {i}",
                description=f"Description {i}",
                chronology_mode="linear"
            )
        )
    
    worlds, total = await world_repo.list_by_user(test_user)
    
    assert total == 3
    assert len(worlds) == 3


@pytest.mark.asyncio
async def test_update_world(
    world_repo: WorldRepository,
    test_user: str,
    sample_world_data: WorldCreate
):
    """Test updating world information."""
    created_world = await world_repo.create(test_user, sample_world_data)
    
    update_data = WorldUpdate(name="Updated World Name")
    updated_world = await world_repo.update(created_world.id, update_data)
    
    assert updated_world is not None
    assert updated_world.name == "Updated World Name"


@pytest.mark.asyncio
async def test_delete_world(
    world_repo: WorldRepository,
    test_user: str,
    sample_world_data: WorldCreate
):
    """Test deleting a world."""
    created_world = await world_repo.create(test_user, sample_world_data)
    
    deleted = await world_repo.delete(created_world.id)
    assert deleted is True
    
    retrieved_world = await world_repo.get_by_id(created_world.id)
    assert retrieved_world is None
```

---

### **MILESTONE 1.3: WorldEvent Model & Repository**

#### **Deliverables**
- WorldEvent model for global timeline
- WorldEvent repository
- Migration with foreign key to worlds
- Unit and integration tests

#### **Step-by-Step Instructions**

**Step 1.3.1: WorldEvent Model (`backend/src/shinkei/models/world_event.py`)**
```python
"""WorldEvent model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from src.shinkei.database.engine import Base
import uuid


class WorldEvent(Base):
    """
    WorldEvent model representing a canonical event in world's timeline.
    
    Attributes:
        id: Unique identifier
        world_id: Foreign key to world
        t: Objective timestamp (can be int or float for flexible time systems)
        label_time: Human-readable time label (e.g., "Log 0017", "Day 42")
        location_id: Optional reference to location (for future GraphRAG)
        type: Event type (incident, glitch, meeting, etc.)
        summary: Brief description of the event
        tags: Array of tags for categorization
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "world_events"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="WorldEvent UUID"
    )
    
    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID this event belongs to"
    )
    
    t: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Objective timestamp in world time"
    )
    
    label_time: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable time label"
    )
    
    location_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Location reference (for future GraphRAG)"
    )
    
    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Event type (incident, glitch, meeting, etc.)"
    )
    
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Brief description of the event"
    )
    
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Tags for categorization"
    )
    
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
    world: Mapped["World"] = relationship("World", back_populates="world_events")
    # story_beats: Mapped[list["StoryBeat"]] = relationship(back_populates="world_event")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('ix_world_events_world_t', 'world_id', 't'),
        Index('ix_world_events_type', 'type'),
    )
    
    def __repr__(self) -> str:
        return f"<WorldEvent(id={self.id}, world_id={self.world_id}, t={self.t}, label_time={self.label_time})>"
```

**Complete WorldEvent implementation with schemas, repository, and tests following the same pattern as User and World models.**

---

### **MILESTONE 1.4: Story Model & Repository**

**Step 1.4.1: Story Model (`backend/src/shinkei/models/story.py`)**
```python
"""Story model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, ForeignKey, DateTime, Float, 
    func, Enum as SQLEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.shinkei.database.engine import Base
import uuid
import enum


class StoryStatus(str, enum.Enum):
    """Story status enumeration."""
    ONGOING = "ongoing"
    PAUSED = "paused"
    FINISHED = "finished"
    BRANCHED = "branched"


class POVType(str, enum.Enum):
    """Point of view type enumeration."""
    OMNISCIENT = "omniscient"
    CHARACTER = "character"
    MODULE = "module"


class TimelineMode(str, enum.Enum):
    """Timeline mode enumeration."""
    JOURNAL = "journal"
    CHAPTERS = "chapters"


class AuthoringMode(str, enum.Enum):
    """Authoring mode enumeration."""
    AUTO = "auto"
    COLLAB = "collab"
    MANUAL = "manual"


class Story(Base):
    """
    Story model representing a subjective narrative within a world.
    
    Attributes:
        id: Unique identifier
        world_id: Foreign key to world
        title: Story title
        synopsis_start: Initial synopsis
        status: Current status (ongoing, paused, finished, branched)
        pov_type: Point of view type
        pov_character_id: Character ID if POV is character-based
        world_time_anchor: Optional global position in world timeline
        timeline_mode: How the story is structured (journal, chapters)
        mode: Authoring mode (auto, collab, manual)
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "stories"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Story UUID"
    )
    
    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID this story belongs to"
    )
    
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Story title"
    )
    
    synopsis_start: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Initial synopsis"
    )
    
    status: Mapped[StoryStatus] = mapped_column(
        SQLEnum(StoryStatus),
        nullable=False,
        default=StoryStatus.ONGOING,
        comment="Current status"
    )
    
    pov_type: Mapped[POVType] = mapped_column(
        SQLEnum(POVType),
        nullable=False,
        default=POVType.OMNISCIENT,
        comment="Point of view type"
    )
    
    pov_character_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Character ID for character POV"
    )
    
    world_time_anchor: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Optional global position in world timeline"
    )
    
    timeline_mode: Mapped[TimelineMode] = mapped_column(
        SQLEnum(TimelineMode),
        nullable=False,
        default=TimelineMode.JOURNAL,
        comment="Story structure mode"
    )
    
    mode: Mapped[AuthoringMode] = mapped_column(
        SQLEnum(AuthoringMode),
        nullable=False,
        default=AuthoringMode.COLLAB,
        comment="Authoring mode"
    )
    
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
    world: Mapped["World"] = relationship("World", back_populates="stories")
    # story_beats: Mapped[list["StoryBeat"]] = relationship(back_populates="story")
    
    __table_args__ = (
        Index('ix_stories_world_status', 'world_id', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<Story(id={self.id}, title={self.title}, world_id={self.world_id})>"
```

---

### **MILESTONE 1.5: StoryBeat Model & Repository**

**Step 1.5.1: StoryBeat Model (`backend/src/shinkei/models/story_beat.py`)**
```python
"""StoryBeat model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, Integer, ForeignKey, DateTime, 
    func, Enum as SQLEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.shinkei.database.engine import Base
import uuid
import enum


class BeatType(str, enum.Enum):
    """Story beat type enumeration."""
    SCENE = "scene"
    LOG = "log"
    MONOLOGUE = "monologue"
    MEMORY = "memory"
    DREAM = "dream"


class GeneratedBy(str, enum.Enum):
    """Generation source enumeration."""
    AI = "ai"
    USER = "user"
    MIXED = "mixed"


class StoryBeat(Base):
    """
    StoryBeat model representing a narrative fragment/log entry.
    
    Attributes:
        id: Unique identifier
        story_id: Foreign key to story
        seq_in_story: Absolute order in the story
        world_event_id: Optional link to WorldEvent (null for dreams/flashbacks)
        local_time_label: In-story time label (e.g., "Entry 003")
        type: Beat type (scene, log, monologue, memory, dream)
        text: The actual narrative content
        summary: Brief summary of the beat
        generated_by: Who created this (ai, user, mixed)
        created_at: Timestamp of creation
    """
    __tablename__ = "story_beats"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="StoryBeat UUID"
    )
    
    story_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Story ID this beat belongs to"
    )
    
    seq_in_story: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Absolute order in the story"
    )
    
    world_event_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("world_events.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional link to WorldEvent"
    )
    
    local_time_label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="In-story time label"
    )
    
    type: Mapped[BeatType] = mapped_column(
        SQLEnum(BeatType),
        nullable=False,
        default=BeatType.SCENE,
        comment="Beat type"
    )
    
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Narrative content"
    )
    
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Brief summary"
    )
    
    generated_by: Mapped[GeneratedBy] = mapped_column(
        SQLEnum(GeneratedBy),
        nullable=False,
        default=GeneratedBy.AI,
        comment="Generation source"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp of creation"
    )
    
    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="story_beats")
    world_event: Mapped[Optional["WorldEvent"]] = relationship(
        "WorldEvent",
        back_populates="story_beats"
    )
    
    __table_args__ = (
        Index('ix_story_beats_story_seq', 'story_id', 'seq_in_story', unique=True),
        Index('ix_story_beats_world_event', 'world_event_id'),
    )
    
    def __repr__(self) -> str:
        return f"<StoryBeat(id={self.id}, story_id={self.story_id}, seq={self.seq_in_story})>"
```

**Update relationships in other models:**
```python
# In World model:
world_events: Mapped[list["WorldEvent"]] = relationship(back_populates="world", cascade="all, delete-orphan")
stories: Mapped[list["Story"]] = relationship(back_populates="world", cascade="all, delete-orphan")

# In WorldEvent model:
story_beats: Mapped[list["StoryBeat"]] = relationship(back_populates="world_event")

# In Story model:
story_beats: Mapped[list["StoryBeat"]] = relationship(back_populates="story", cascade="all, delete-orphan", order_by="StoryBeat.seq_in_story")
```

---

## **PHASE 1 COMPLETION CHECKLIST**

### **Deliverables Verification**
- [ ] User model and repository complete with tests
- [ ] World model and repository complete with tests
- [ ] WorldEvent model and repository complete with tests
- [ ] Story model and repository complete with tests
- [ ] StoryBeat model and repository complete with tests
- [ ] All migrations applied successfully
- [ ] All relationships properly configured
- [ ] Repository pattern implemented consistently
- [ ] Unit test coverage ≥ 80% per model
- [ ] Integration tests for all repositories
- [ ] Database indexes optimized

### **Testing Checklist**
- [ ] All CRUD operations tested for each model
- [ ] Cascade deletes working correctly
- [ ] Foreign key constraints enforced
- [ ] Unique constraints working
- [ ] Pagination working for list operations
- [ ] Complex queries tested (joins, filters)

---

# **PHASE 2: AUTHENTICATION & SECURITY**

## **Duration**: 5-7 days
## **Goal**: Implement Supabase Auth integration with JWT validation and authorization

---

### **MILESTONE 2.1: Supabase Auth Integration**

#### **Deliverables**
- Supabase client setup
- JWT validation middleware
- Auth dependencies for FastAPI
- User synchronization with Supabase

#### **Step-by-Step Instructions**

**Step 2.1.1: Supabase Client (`backend/src/shinkei/auth/supabase_client.py`)**
```python
"""Supabase client configuration."""
from supabase import create_client, Client
from src.shinkei.config import settings
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


def get_supabase_client() -> Client:
    """
    Get Supabase client instance.
    
    Returns:
        Configured Supabase client
    """
    if not settings.supabase_url or not settings.supabase_key:
        logger.warning("supabase_credentials_missing")
        raise ValueError("Supabase credentials not configured")
    
    return create_client(settings.supabase_url, settings.supabase_key)


# Global client instance
supabase: Client = get_supabase_client() if settings.supabase_url else None
```

**Step 2.1.2: JWT Validation (`backend/src/shinkei/auth/jwt.py`)**
```python
"""JWT token validation and user extraction."""
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from src.shinkei.config import settings
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


class TokenData:
    """Decoded token data."""
    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email


def decode_token(token: str) -> TokenData:
    """
    Decode and validate JWT token from Supabase.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[settings.algorithm],
            options={"verify_aud": False}  # Supabase tokens don't have aud
        )
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            logger.warning("token_missing_claims")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(user_id=user_id, email=email)
        
    except JWTError as e:
        logger.error("jwt_decode_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_token_from_header(authorization: Optional[str]) -> str:
    """
    Extract JWT token from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        JWT token string
        
    Raises:
        HTTPException: If header is missing or malformed
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    parts = authorization.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return parts[1]
```

**Step 2.1.3: Auth Dependencies (`backend/src/shinkei/auth/dependencies.py`)**
```python
"""FastAPI dependencies for authentication."""
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.auth.jwt import decode_token, extract_token_from_header
from src.shinkei.database.engine import get_db
from src.shinkei.models.user import User
from src.shinkei.repositories.user import UserRepository
from src.shinkei.schemas.user import UserCreate
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user.
    
    This dependency:
    1. Validates the JWT token from Supabase
    2. Gets or creates the user in our database
    3. Returns the User model instance
    
    Args:
        authorization: Authorization header
        session: Database session
        
    Returns:
        User instance
        
    Raises:
        HTTPException: If authentication fails
    """
    # Extract and decode token
    token = extract_token_from_header(authorization)
    token_data = decode_token(token)
    
    # Get or create user in our database
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(token_data.user_id)
    
    if not user:
        # Sync user from Supabase to our database
        logger.info("creating_user_from_token", user_id=token_data.user_id)
        user = await user_repo.create(
            UserCreate(
                id=token_data.user_id,
                email=token_data.email,
                name=token_data.email.split("@")[0]  # Default name from email
            )
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (future: could check if user is disabled).
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Active user instance
    """
    # Future: Add user status checks here
    return current_user
```

**Step 2.1.4: Update Main App with Auth (`backend/src/shinkei/main.py`)**
```python
# Add authentication info to OpenAPI docs
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True
    },
)

# Add security scheme to OpenAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add security to all routes
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
```

#### **Unit Tests**

**Test File: `backend/tests/unit/test_auth_jwt.py`**
```python
"""Unit tests for JWT validation."""
import pytest
from jose import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from src.shinkei.auth.jwt import decode_token, extract_token_from_header
from src.shinkei.config import settings


def create_test_token(user_id: str, email: str, expired: bool = False) -> str:
    """Create a test JWT token."""
    expire = datetime.utcnow() + timedelta(
        minutes=-30 if expired else 30
    )
    
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire
    }
    
    return jwt.encode(payload, settings.supabase_jwt_secret, algorithm=settings.algorithm)


def test_decode_valid_token():
    """Test decoding a valid token."""
    token = create_test_token("user-123", "test@example.com")
    token_data = decode_token(token)
    
    assert token_data.user_id == "user-123"
    assert token_data.email == "test@example.com"


def test_decode_expired_token():
    """Test decoding an expired token raises exception."""
    token = create_test_token("user-123", "test@example.com", expired=True)
    
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    
    assert exc_info.value.status_code == 401


def test_extract_token_from_header_valid():
    """Test extracting token from valid header."""
    header = "Bearer test-token-123"
    token = extract_token_from_header(header)
    
    assert token == "test-token-123"


def test_extract_token_from_header_missing():
    """Test extracting token from missing header."""
    with pytest.raises(HTTPException) as exc_info:
        extract_token_from_header(None)
    
    assert exc_info.value.status_code == 401


def test_extract_token_from_header_malformed():
    """Test extracting token from malformed header."""
    with pytest.raises(HTTPException) as exc_info:
        extract_token_from_header("InvalidHeader")
    
    assert exc_info.value.status_code == 401
```

---

### **MILESTONE 2.2: Authorization & Access Control**

#### **Deliverables**
- Resource ownership validation
- Authorization decorators/dependencies
- OWASP BOLA prevention

#### **Step-by-Step Instructions**

**Step 2.2.1: Authorization Utilities (`backend/src/shinkei/auth/authorization.py`)**
```python
"""Authorization and access control utilities."""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.models.user import User
from src.shinkei.repositories.world import WorldRepository
from src.shinkei.repositories.story import StoryRepository
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


async def verify_world_ownership(
    world_id: str,
    user: User,
    session: AsyncSession
) -> None:
    """
    Verify that the user owns the specified world.
    
    Args:
        world_id: World UUID
        user: Current user
        session: Database session
        
    Raises:
        HTTPException: If world not found or not owned by user
    """
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(user.id, world_id)
    
    if not world:
        logger.warning(
            "unauthorized_world_access_attempt",
            user_id=user.id,
            world_id=world_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found"
        )


async def verify_story_ownership(
    story_id: str,
    user: User,
    session: AsyncSession
) -> None:
    """
    Verify that the user owns the story (via world ownership).
    
    Args:
        story_id: Story UUID
        user: Current user
        session: Database session
        
    Raises:
        HTTPException: If story not found or not owned by user
    """
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_id(story_id)
    
    if not story:
        logger.warning(
            "unauthorized_story_access_attempt",
            user_id=user.id,
            story_id=story_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )
    
    # Verify world ownership
    await verify_world_ownership(story.world_id, user, session)


class ResourceOwnershipValidator:
    """Helper class for validating resource ownership."""
    
    def __init__(self, session: AsyncSession, user: User):
        """
        Initialize validator.
        
        Args:
            session: Database session
            user: Current user
        """
        self.session = session
        self.user = user
    
    async def validate_world(self, world_id: str) -> None:
        """Validate world ownership."""
        await verify_world_ownership(world_id, self.user, self.session)
    
    async def validate_story(self, story_id: str) -> None:
        """Validate story ownership."""
        await verify_story_ownership(story_id, self.user, self.session)
```

**Step 2.2.2: Security Headers Middleware (`backend/src/shinkei/middleware/security.py`)**
```python
"""Security headers middleware."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response: Response = await call_next(request)
        
        # OWASP recommended security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self';"
        )
        
        return response
```

**Add middleware to main app:**
```python
from src.shinkei.middleware.security import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

#### **Unit Tests**

**Test File: `backend/tests/unit/test_authorization.py`**
```python
"""Unit tests for authorization."""
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.auth.authorization import verify_world_ownership
from src.shinkei.models.user import User
from src.shinkei.models.world import World
from src.shinkei.repositories.world import WorldRepository
from src.shinkei.schemas.world import WorldCreate


@pytest.mark.asyncio
async def test_verify_world_ownership_valid(db_session: AsyncSession):
    """Test valid world ownership verification."""
    # Create user
    user = User(id="user-1", email="test@example.com", name="Test")
    db_session.add(user)
    await db_session.commit()
    
    # Create world
    world_repo = WorldRepository(db_session)
    world = await world_repo.create(user.id, WorldCreate(name="Test World"))
    
    # Should not raise
    await verify_world_ownership(world.id, user, db_session)


@pytest.mark.asyncio
async def test_verify_world_ownership_invalid(db_session: AsyncSession):
    """Test invalid world ownership verification raises exception."""
    # Create two users
    user1 = User(id="user-1", email="test1@example.com", name="Test 1")
    user2 = User(id="user-2", email="test2@example.com", name="Test 2")
    db_session.add_all([user1, user2])
    await db_session.commit()
    
    # Create world for user1
    world_repo = WorldRepository(db_session)
    world = await world_repo.create(user1.id, WorldCreate(name="Test World"))
    
    # User2 trying to access user1's world should raise
    with pytest.raises(HTTPException) as exc_info:
        await verify_world_ownership(world.id, user2, db_session)
    
    assert exc_info.value.status_code == 404
```

---

## **PHASE 2 COMPLETION CHECKLIST**

- [ ] Supabase client configured
- [ ] JWT validation working
- [ ] Auth dependencies implemented
- [ ] User synchronization from Supabase working
- [ ] Authorization utilities complete
- [ ] BOLA prevention implemented
- [ ] Security headers middleware added
- [ ] All auth unit tests passing
- [ ] Integration tests with protected endpoints
- [ ] Security audit clean

---

# **PHASE 3: CORE CRUD OPERATIONS & API ENDPOINTS**

## **Duration**: 7-10 days
## **Goal**: Implement RESTful API endpoints for all core models

---

### **MILESTONE 3.1: User API Endpoints**

#### **Deliverables**
- User CRUD endpoints
- Profile management
- Settings update
- Full OpenAPI documentation

#### **Step-by-Step Instructions**

**Step 3.1.1: User API Router (`backend/src/shinkei/api/v1/endpoints/users.py`)**
```python
"""User API endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.auth.dependencies import get_current_active_user
from src.shinkei.database.engine import get_db
from src.shinkei.models.user import User
from src.shinkei.repositories.user import UserRepository
from src.shinkei.schemas.user import UserResponse, UserUpdate
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get current user's profile.
    
    Returns:
        Current user information
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update current user's profile.
    
    Args:
        user_data: Updated user data
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Updated user information
    """
    user_repo = UserRepository(session)
    updated_user = await user_repo.update(current_user.id, user_data)
    
    logger.info("user_profile_updated", user_id=current_user.id)
    return UserResponse.model_validate(updated_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete current user's account.
    
    This will cascade delete all user's worlds, stories, and beats.
    
    Args:
        current_user: Current authenticated user
        session: Database session
    """
    user_repo = UserRepository(session)
    await user_repo.delete(current_user.id)
    
    logger.info("user_account_deleted", user_id=current_user.id)
```

**Step 3.1.2: API Router Configuration (`backend/src/shinkei/api/v1/router.py`)**
```python
"""API v1 router configuration."""
from fastapi import APIRouter
from src.shinkei.api.v1.endpoints import users, worlds, stories, story_beats

api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(users.router)
api_router.include_router(worlds.router)
api_router.include_router(stories.router)
api_router.include_router(story_beats.router)
```

**Update main.py to include API router:**
```python
from src.shinkei.api.v1.router import api_router

app.include_router(api_router)
```

---

### **MILESTONE 3.2: World API Endpoints**

**Step 3.2.1: World API Router (`backend/src/shinkei/api/v1/endpoints/worlds.py`)**
```python
"""World API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.auth.dependencies import get_current_active_user
from src.shinkei.auth.authorization import verify_world_ownership
from src.shinkei.database.engine import get_db
from src.shinkei.models.user import User
from src.shinkei.repositories.world import WorldRepository
from src.shinkei.schemas.world import (
    WorldCreate,
    WorldResponse,
    WorldUpdate,
    WorldListResponse
)
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/worlds", tags=["worlds"])


@router.post(
    "",
    response_model=WorldResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_world(
    world_data: WorldCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> WorldResponse:
    """
    Create a new world.
    
    Args:
        world_data: World creation data
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Created world
    """
    world_repo = WorldRepository(session)
    world = await world_repo.create(current_user.id, world_data)
    
    logger.info("world_created", world_id=world.id, user_id=current_user.id)
    return WorldResponse.model_validate(world)


@router.get("", response_model=WorldListResponse)
async def list_worlds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> WorldListResponse:
    """
    List all worlds owned by current user.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Paginated list of worlds
    """
    world_repo = WorldRepository(session)
    skip = (page - 1) * page_size
    
    worlds, total = await world_repo.list_by_user(
        current_user.id,
        skip=skip,
        limit=page_size
    )
    
    return WorldListResponse(
        worlds=[WorldResponse.model_validate(w) for w in worlds],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{world_id}", response_model=WorldResponse)
async def get_world(
    world_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> WorldResponse:
    """
    Get a specific world.
    
    Args:
        world_id: World UUID
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        World details
    """
    await verify_world_ownership(world_id, current_user, session)
    
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_id(world_id)
    
    return WorldResponse.model_validate(world)


@router.put("/{world_id}", response_model=WorldResponse)
async def update_world(
    world_id: str,
    world_data: WorldUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> WorldResponse:
    """
    Update a world.
    
    Args:
        world_id: World UUID
        world_data: World update data
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Updated world
    """
    await verify_world_ownership(world_id, current_user, session)
    
    world_repo = WorldRepository(session)
    world = await world_repo.update(world_id, world_data)
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    logger.info("world_updated", world_id=world_id, user_id=current_user.id)
    return WorldResponse.model_validate(world)


@router.delete("/{world_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_world(
    world_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a world and all associated data.
    
    Args:
        world_id: World UUID
        current_user: Current authenticated user
        session: Database session
    """
    await verify_world_ownership(world_id, current_user, session)
    
    world_repo = WorldRepository(session)
    await world_repo.delete(world_id)
    
    logger.info("world_deleted", world_id=world_id, user_id=current_user.id)
```

---

### **MILESTONE 3.3-3.5: Story, StoryBeat, and WorldEvent Endpoints**

Follow the same pattern for:
- Stories API endpoints with world ownership validation
- StoryBeats API endpoints with story ownership validation
- WorldEvents API endpoints with world ownership validation

Each should include:
- Full CRUD operations
- Proper authorization
- Pagination for list operations
- Comprehensive error handling
- Logging

---

### **Integration Tests for API Endpoints**

**Test File: `backend/tests/integration/test_api_worlds.py`**
```python
"""Integration tests for World API endpoints."""
import pytest
from httpx import AsyncClient
from src.shinkei.main import app
from src.shinkei.auth.jwt import create_test_token


@pytest.fixture
def auth_headers():
    """Create authorization headers with test token."""
    token = create_test_token("test-user-id", "test@example.com")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_world(auth_headers):
    """Test creating a new world."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/worlds",
            json={
                "name": "Test World",
                "description": "A test world",
                "chronology_mode": "linear"
            },
            headers=auth_headers
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test World"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_worlds(auth_headers):
    """Test listing worlds."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/worlds",
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "worlds" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_world_unauthorized():
    """Test getting a world without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/worlds/some-id")
    
    assert response.status_code == 401
```

---

## **PHASE 3 COMPLETION CHECKLIST**

- [ ] All CRUD endpoints implemented for all models
- [ ] Authorization working on all protected endpoints
- [ ] Pagination working correctly
- [ ] OpenAPI documentation complete and accurate
- [ ] Input validation working
- [ ] Error handling comprehensive
- [ ] Integration tests for all endpoints
- [ ] Postman/Thunder Client collection created

---

# **PHASE 4-12: REMAINING PHASES SUMMARY**

Due to space constraints, here's the structure for remaining phases:

## **PHASE 4: AI ENGINE FOUNDATION** (7-10 days)
- Abstract NarrativeModel interface
- Local LLM integration (LocalAI, Ollama)
- API-based LLM integration (OpenAI, Anthropic)
- Model selection and configuration
- Prompt engineering utilities
- Unit tests for all AI integrations

## **PHASE 5: NARRATIVE GENERATION PIPELINE** (10-14 days)
- GenerationContext builder
- Beat generation pipeline
- Summary generation
- Coherence validation
- Integration with world laws and tone
- Generation history tracking

## **PHASE 6: FRONTEND FOUNDATION** (10-14 days)
- SvelteKit app structure
- Supabase Auth integration
- API client setup
- State management (stores)
- Component library setup
- Routing structure
- Theme system (light/dark mode)

## **PHASE 7: WORLD & TIMELINE MANAGEMENT UI** (7-10 days)
- World list view
- World detail view
- World creation/edit forms
- Timeline visualization
- WorldEvent management
- Cross-story intersection visualization

## **PHASE 8: STORY MANAGEMENT UI** (7-10 days)
- Story list view
- Story detail view
- Story creation/edit forms
- Beat list/journal view
- Mode selector UI
- POV configuration

## **PHASE 9: MULTI-MODE AUTHORING SYSTEM** (14-21 days)
- **Auto Mode**: Fully automated generation
- **Collaborative Mode**: User guidance, AI proposals, editing
- **Manual Mode**: User writing with AI assistance
- Mode switching logic
- Generation controls
- Real-time preview

## **PHASE 10: CROSS-STORY INTERSECTIONS** (7-10 days)
- Shared WorldEvent detection
- Story intersection UI
- Timeline synchronization
- Coherence enforcement across stories

## **PHASE 11: GRAPHRAG PREPARATION** (10-14 days)
- Character, Location, Concept models
- Linking tables
- Entity extraction pipeline
- Graph query utilities
- Visualization preparation

## **PHASE 12: PRODUCTION READINESS** (14-21 days)
- Performance optimization
- Caching layer (Redis)
- Rate limiting
- Monitoring and alerting (OpenTelemetry + Grafana)
- Production deployment (Docker, Kubernetes)
- Backup and recovery procedures
- Documentation finalization
- User acceptance testing

---

# **PROJECT TIMELINE SUMMARY**

| Phase | Duration | Cumulative Days |
|-------|----------|-----------------|
| Phase 0: Foundation | 3-5 days | 5 |
| Phase 1: Database Layer | 5-7 days | 12 |
| Phase 2: Authentication | 5-7 days | 19 |
| Phase 3: CRUD API | 7-10 days | 29 |
| Phase 4: AI Engine | 7-10 days | 39 |
| Phase 5: Generation Pipeline | 10-14 days | 53 |
| Phase 6: Frontend Foundation | 10-14 days | 67 |
| Phase 7: World UI | 7-10 days | 77 |
| Phase 8: Story UI | 7-10 days | 87 |
| Phase 9: Multi-Mode System | 14-21 days | 108 |
| Phase 10: Intersections | 7-10 days | 118 |
| Phase 11: GraphRAG Prep | 10-14 days | 132 |
| Phase 12: Production | 14-21 days | 153 |

**Total Estimated Time: 5-6 months of focused development**

---

# **DAILY DEVELOPMENT WORKFLOW**

## **For Claude Code:**

### **Start of Day**
1. Pull latest changes from repository
2. Review current phase checklist
3. Run all existing tests to ensure stability
4. Review implementation plan for current milestone

### **Development Cycle** (per feature/milestone)
1. **Write Tests First** - Create unit tests for new functionality
2. **Implement Feature** - Write minimal code to pass tests
3. **Refactor** - Improve code quality while keeping tests green
4. **Integration Test** - Test feature in context
5. **Document** - Update inline documentation and API docs
6. **Commit** - Commit with descriptive message

### **End of Day**
1. Run full test suite
2. Run security scanner
3. Update progress in checklist
4. Push to repository
5. Document any blockers or questions

---

# **DEVELOPMENT BEST PRACTICES**

## **Code Quality**
- Follow PEP 8 (Python) and TypeScript style guides
- Use type hints everywhere
- Keep functions small and focused (< 50 lines)
- Avoid code duplication (DRY principle)
- Comment complex logic, not obvious code

## **Testing**
- Aim for 80%+ code coverage
- Test happy paths and error cases
- Use fixtures for test data
- Mock external dependencies
- Test edge cases

## **Security**
- Never commit secrets
- Always validate user input
- Use parameterized queries
- Implement rate limiting on sensitive endpoints
- Log security events
- Regular dependency updates

## **Performance**
- Use database indexes for frequent queries
- Implement pagination for list endpoints
- Cache expensive operations
- Use async/await properly
- Profile before optimizing

## **Git Workflow**
- Create feature branches for each milestone
- Write descriptive commit messages
- Squash commits before merging to main
- Tag releases with semantic versioning
- Keep main branch always deployable

---

# **TROUBLESHOOTING GUIDE**

## **Common Issues**

### **Database Connection Failures**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### **Migration Conflicts**
```bash
# Rollback to previous migration
alembic downgrade -1

# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

### **Test Failures**
```bash
# Run specific test file
pytest tests/unit/test_specific.py -v

# Run with debugging
pytest tests/ -v -s --pdb

# Check coverage
pytest --cov --cov-report=html
```

### **Import Errors**
```bash
# Reinstall dependencies
poetry install

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

# **COMPLETION CRITERIA**

The project is considered complete when:

1. ✅ All 12 phases completed
2. ✅ All unit tests passing (≥80% coverage)
3. ✅ All integration tests passing
4. ✅ All E2E tests passing
5. ✅ Security audit clean (OWASP Top 10)
6. ✅ Performance benchmarks met
7. ✅ Documentation complete
8. ✅ Deployed to production environment
9. ✅ User acceptance testing passed
10. ✅ All critical bugs resolved

---

# **NEXT STEPS FOR CLAUDE CODE**

1. **Start with Phase 0, Milestone 0.1**
2. Follow instructions step-by-step
3. Complete each testing checklist
4. Only move to next milestone after all tests pass
5. Document any deviations from the plan
6. Ask for clarification if instructions are ambiguous

**Remember**: Quality over speed. It's better to have a solid foundation than to rush through and accumulate technical debt.

---

# **APPENDIX A: USEFUL COMMANDS**

```bash
# Backend Development
cd backend
poetry install                    # Install dependencies
poetry run pytest                 # Run tests
poetry run black .                # Format code
poetry run ruff check .           # Lint code
poetry run mypy src/              # Type check
poetry run alembic upgrade head   # Apply migrations
poetry run uvicorn src.shinkei.main:app --reload  # Start server

# Frontend Development
cd frontend
npm install                       # Install dependencies
npm run dev                       # Start dev server
npm test                          # Run tests
npm run lint                      # Lint code
npm run format                    # Format code
npm run build                     # Build for production

# Docker
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs -f backend    # View backend logs
docker-compose exec postgres psql -U shinkei_user -d shinkei  # Access DB

# Git
git checkout -b feature/milestone-X  # Create feature branch
git add .                            # Stage changes
git commit -m "feat: description"    # Commit with message
git push origin feature/milestone-X  # Push branch
```

---

# **APPENDIX B: RESOURCES**

## **Documentation**
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Supabase: https://supabase.com/docs
- SvelteKit: https://kit.svelte.dev/docs
- PostgreSQL: https://www.postgresql.org/docs/

## **Security**
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP API Security: https://owasp.org/www-project-api-security/

## **Testing**
- Pytest: https://docs.pytest.org/
- Vitest: https://vitest.dev/

---

**END OF IMPLEMENTATION PLAN**

This plan is a living document. Update it as the project evolves and new requirements emerge.

