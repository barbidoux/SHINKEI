# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Shinkei (心継)** is a narrative engine for generating, co-authoring, and manually writing interconnected inner worlds. Users create "Worlds" containing "Stories" made of sequential "StoryBeats". Stories can intersect through shared "WorldEvents" on a global timeline.

### Core Concept
- **Worlds**: Self-contained narrative universes with tone, laws, and backdrop
- **Stories**: Subjective narrative arcs within a world (Auto/Collaborative/Manual modes)
- **StoryBeats**: Sequential narrative fragments (scenes, logs, memories)
- **WorldEvents**: Canonical events on the global timeline where stories can intersect

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL via SQLAlchemy 2.0
- **Migrations**: Alembic
- **Auth**: Supabase (JWT-based)
- **AI Providers**: OpenAI, Anthropic, Ollama (via abstract NarrativeModel interface)
- **Testing**: Pytest with pytest-asyncio
- **Code Quality**: Black, Ruff, Mypy

### Frontend
- **Framework**: SvelteKit (Node 20+)
- **Styling**: TailwindCSS + PostCSS + Autoprefixer
- **Components**: Bits UI
- **Auth**: Supabase client
- **Testing**: Vitest + Testing Library

### Infrastructure
- **Local Development**: Docker Compose
- **Database**: Supabase (PostgreSQL)
- **Observability**: OpenTelemetry + SigNoz (optional)

## Project Structure

```
shinkei/
├── backend/                    # FastAPI Modular Monolith
│   ├── src/shinkei/
│   │   ├── api/v1/            # API endpoints
│   │   │   └── endpoints/     # Route handlers (users, worlds, stories, etc.)
│   │   ├── auth/              # Authentication & authorization
│   │   ├── database/          # DB engine & session management
│   │   ├── generation/        # AI generation engine
│   │   │   ├── base.py        # Abstract NarrativeModel interface
│   │   │   ├── factory.py     # Provider factory
│   │   │   ├── service.py     # Generation service
│   │   │   ├── prompts.py     # Prompt templates
│   │   │   └── providers/     # OpenAI, Anthropic, Ollama implementations
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── repositories/      # Data access layer
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── config.py          # Settings management
│   │   ├── logging_config.py  # Structured logging
│   │   └── main.py            # FastAPI application entry
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Pytest test suite
│   │   ├── unit/
│   │   ├── integration/
│   │   └── api/
│   ├── pyproject.toml         # Poetry dependencies
│   └── alembic.ini
├── frontend/                   # SvelteKit application
│   └── package.json
├── docker/                     # Container configurations
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── IMPLEMENTATION_PLAN/        # Detailed implementation guides
```

## Development Commands

### Backend

**Setup & Dependencies:**
```bash
cd backend
poetry install
```

**Database Migrations:**
```bash
# Run migrations
poetry run alembic upgrade head

# Create new migration
poetry run alembic revision --autogenerate -m "description"
```

**Run Development Server:**
```bash
# Via Docker (recommended - includes PostgreSQL)
docker-compose -f docker/docker-compose.yml up backend

# Or locally (requires PostgreSQL running)
cd backend
poetry run uvicorn src.shinkei.main:app --reload
```

**Testing:**
```bash
cd backend
poetry run pytest                    # Run all tests
poetry run pytest tests/unit/        # Unit tests only
poetry run pytest tests/integration/ # Integration tests only
poetry run pytest -v --cov           # With coverage report
```

**Code Quality:**
```bash
poetry run black .              # Format code
poetry run ruff check .         # Lint
poetry run mypy src/            # Type checking
```

**Run a Single Test:**
```bash
poetry run pytest tests/unit/test_config.py              # Run specific test file
poetry run pytest tests/api/test_users.py::test_name     # Run specific test function
poetry run pytest -k "test_pattern"                       # Run tests matching pattern
```

### Frontend

**Setup & Dependencies:**
```bash
cd frontend
npm install
```

**Run Development Server:**
```bash
# Via Docker
docker-compose -f docker/docker-compose.yml up frontend

# Or locally
npm run dev
```

**Testing & Quality:**
```bash
npm test               # Run Vitest tests
npm run check          # SvelteKit type checking
npm run lint           # ESLint
npm run format         # Prettier formatting
```

### Full Stack (Docker)

```bash
# Start all services (PostgreSQL, Backend, Frontend)
docker-compose -f docker/docker-compose.yml up

# Start specific service
docker-compose -f docker/docker-compose.yml up backend

# View logs
docker-compose -f docker/docker-compose.yml logs -f backend

# Stop all services
docker-compose -f docker/docker-compose.yml down
```

## Architecture Patterns

### Modular Monolith
The backend follows a modular monolith pattern with domain-driven modules. Key principles:
- **No cross-module DB joins**: Use internal API facades instead
- **Repositories for data access**: Models should not contain business logic
- **Pydantic schemas for validation**: Separate from SQLAlchemy models
- **Dependency injection**: Use FastAPI's dependency system

### Database Schema Evolution
- **"Expand and Contract" migrations**: Never break existing code
- **GraphRAG-ready**: Schema supports future entity graph features
- **Explicit ownership checks**: All entities verify `user_id` ownership

### Data Model Hierarchy
```
User
  └── World (tone, laws, backdrop, chronology_mode)
      ├── WorldEvent (t, label_time, location, type, summary)
      └── Story (title, synopsis, status, pov_type, mode, tags, archived_at)
          └── StoryBeat (seq_in_story, world_event_id, type, text, generated_by)
```

### Story Management Features (Fully Implemented)

**Feature 1: Story Metadata Editing**
- Full edit page UI with all fields (title, synopsis, theme, status, mode, POV, tags)
- Backend: Complete CRUD with validation
- Frontend: `/stories/[id]/edit` route with form validation

**Feature 2: Story Tags**
- PostgreSQL ARRAY column with GIN index for fast queries
- Tag autocomplete from existing world tags
- Tag filtering in story lists
- Max 20 tags per story, 50 chars each

**Feature 3: Story Templates**
- 8 genre presets: sci-fi-thriller, epic-fantasy, survival-horror, mystery-detective, etc.
- Template selector in creation form
- Auto-fills synopsis, theme, mode, POV, suggested tags
- Located in `backend/src/shinkei/generation/story_templates.py`

**Feature 4: Story Statistics**
- Real-time calculation from beat data
- Metrics: word count, beat count, character count, reading time
- Authoring distribution (AI vs user vs collaborative)
- Beat type distribution
- Estimated reading time (250 words/minute)

**Feature 5: Story Cloning**
- Deep copy with new UUIDs
- Preserves all beats and event links
- Appends " (Copy)" to title
- Maintains beat order and sequence

**Feature 6: Story Archiving**
- Soft delete via `archived_at` timestamp
- Restore functionality
- Archived stories page per world
- Status automatically set to "archived"

### Three Temporal Layers
1. **`t`**: Objective world time (WorldEvent.t)
2. **`local_time_label`**: In-world narrative timestamp ("Log 0017")
3. **`seq_in_story`**: Reading order within a story

### Story Intersection
Stories intersect when multiple StoryBeats reference the same `WorldEvent`. This ensures coherent cross-story continuity.

## AI Engine Architecture

The AI generation system is implemented with an abstract `NarrativeModel` interface supporting multiple providers:

**Core Components:**
- **`generation/base.py`**: Abstract `NarrativeModel` interface defining `generate()` and `generate_stream()` methods
- **`generation/factory.py`**: Factory for creating provider instances based on configuration
- **`generation/service.py`**: `GenerationService` orchestrating generation with prompt templates
- **`generation/prompts.py`**: Jinja2-based prompt template management
- **`generation/providers/`**: Provider implementations (OpenAI, Anthropic, Ollama)

**Supported Providers:**
- **OpenAI**: GPT-4, GPT-3.5-turbo (requires `OPENAI_API_KEY`)
- **Anthropic**: Claude models (requires `ANTHROPIC_API_KEY`)
- **Ollama**: Local models (requires Ollama running locally)

**API Endpoint:**
- `POST /api/v1/generation/generate`: Generate content from templates with provider selection

**Configuration:**
Set provider API keys in `.env`:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_LLM_PROVIDER=openai  # or anthropic, ollama
```

**Three Authoring Modes:**
- **Autonomous**: AI generates everything
- **Collaborative**: AI proposes, user edits
- **Manual**: User writes, AI ensures coherence

## Security & Authentication

- **Authentication**: Supabase JWT tokens
- **Backend validation**: Local JWT verification (stateless)
- **Ownership checks**: All repository methods verify user access
- **CORS**: Configured in `config.py` via `cors_origins`

## Configuration

Configuration is managed via Pydantic Settings in [backend/src/shinkei/config.py](backend/src/shinkei/config.py):

- Reads from `.env` file or environment variables
- Key settings: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_KEY`, `SECRET_KEY`
- AI provider keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEFAULT_LLM_PROVIDER`
- Environment modes: `development`, `staging`, `production`
- CORS origins include both `localhost` and `127.0.0.1` on multiple ports (5173-5175, 3000)

## Testing Strategy

- **Unit tests**: Test individual functions/classes (80%+ coverage target)
- **Integration tests**: Test repository layer with real database
- **API tests**: Test endpoints with FastAPI TestClient
- **All tests use pytest-asyncio** for async support

Test fixtures in [backend/tests/conftest.py](backend/tests/conftest.py) provide:
- Database session management
- Test client creation
- Cleanup between tests

## API Endpoints

The backend exposes the following API routers under `/api/v1`:

- `/auth` - Authentication (register, login)
- `/users` - User management
- `/worlds` - World CRUD operations
- `/worlds/{world_id}/events` - WorldEvent management (nested under worlds)
- `/worlds/{world_id}/stories` - Story management (nested under worlds)
  - `GET /worlds/{id}/stories` - List stories (supports `?tag=sci-fi&include_archived=true`)
  - `POST /worlds/{id}/stories` - Create story (with tags, mode, pov_type)
  - `GET /worlds/{id}/stories/archived` - List archived stories
  - `GET /worlds/{id}/stories/tags` - Get all unique tags in world
- `/stories` - Story operations
  - `GET /stories/{id}` - Get story details
  - `PUT /stories/{id}` - Update story
  - `DELETE /stories/{id}` - Archive story (soft delete)
  - `GET /stories/templates` - List story templates
  - `POST /stories/{id}/clone` - Clone story with all beats
  - `POST /stories/{id}/restore` - Restore archived story
  - `GET /stories/{id}/statistics` - Get story statistics
- `/stories/{story_id}/beats` - StoryBeat management (nested under stories)
- `/generation` - AI content generation
- `/health` - Health check endpoints (basic, ready, liveness, startup, detailed)

All endpoints require authentication via JWT Bearer tokens (except `/auth` endpoints).

## Important Notes

1. **Never hardcode credentials**: Use environment variables
2. **Always use repositories for data access**: Don't query directly in endpoints
3. **Migration safety**: Test migrations both `upgrade` and `downgrade`
4. **API versioning**: All endpoints under `/api/v1` prefix
5. **Structured logging**: Use `get_logger(__name__)` from `logging_config`
6. **Provider selection**: AI generation supports multiple providers via factory pattern
7. **Enum serialization**: All enums (mode, pov_type, status, generated_by) serialize to lowercase
8. **Password requirements**: Min 12 chars, 1 uppercase, 1 special character
9. **Soft delete**: Stories use `archived_at` timestamp, not hard delete

## Documentation

- **[SHINKEI_SPECS.md](SHINKEI_SPECS.md)**: Full specification document
- **[GEMINI.md](GEMINI.md)**: Quick reference for AI assistants
- **[IMPLEMENTATION_PLAN/](IMPLEMENTATION_PLAN/)**: Detailed phase-by-phase guides
  - `SHINKEI_IMPLEMENTATION_PLAN.md`: Complete roadmap
  - `SHINKEI_AI_ENGINE_FRONTEND_GUIDE.md`: AI integration guide
  - `SHINKEI_QUICK_START_GUIDE.md`: Quick setup guide

## CI/CD & Automation

### GitHub Actions Workflows

The project uses GitHub Actions for continuous integration and security scanning:

**1. CI Workflow** (`.github/workflows/ci.yml`)
- **Triggers**: Push to main/develop, pull requests
- **Backend Job**:
  - Code quality checks (Black, Ruff, Mypy)
  - Full test suite with coverage
  - PostgreSQL service for integration tests
- **Frontend Job**:
  - Linter and type checking
  - Test execution
  - Production build verification
- **Integration Job**:
  - Database migrations
  - Full integration test suite

**2. Security Scan** (`.github/workflows/security-scan.yml`)
- **Triggers**: Push to main, PRs, weekly schedule
- Trivy filesystem and Docker image scanning
- Bandit Python security linter
- Safety dependency vulnerability checker
- Results uploaded to GitHub Security tab

**3. Docker Build Verification** (`.github/workflows/docker-build.yml`)
- **Triggers**: Changes to Docker files or application code
- Builds and verifies both backend and frontend images
- Tests Docker Compose stack startup
- Verifies health endpoints

### Health Check Endpoints

**Basic Health** (`/health`):
- Application metadata (name, version, environment)
- Database connectivity verification
- Returns 503 if database is unavailable

**Orchestration Probes** (`/api/v1/health/*`):
- **`/ready`**: Readiness probe - indicates when app can receive traffic
- **`/liveness`**: Liveness probe - simple process health check
- **`/startup`**: Startup probe - indicates initial startup completion
- **`/detailed`**: Comprehensive health status with latency metrics

**Usage in Kubernetes/Docker**:
```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health/liveness
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /api/v1/health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

### Running CI Checks Locally

**Backend**:
```bash
cd backend
poetry run black --check .        # Code formatting
poetry run ruff check .            # Linting
poetry run mypy src/               # Type checking
poetry run pytest -v --cov         # Tests with coverage
```

**Security Scans**:
```bash
# Trivy (install first: brew install trivy)
trivy fs .

# Python security
poetry run bandit -r src/
poetry run safety check
```

## Current State

The project has:
- ✅ Backend structure with FastAPI
- ✅ SQLAlchemy models (User, World, Story, StoryBeat, WorldEvent)
- ✅ Alembic migrations (including tags and soft delete)
- ✅ Repository pattern implementation
- ✅ Full API endpoints (auth, users, worlds, stories, events, beats, health)
- ✅ AI generation engine with multi-provider support (OpenAI, Anthropic, Ollama)
- ✅ Generation service with prompt template system
- ✅ Docker Compose setup
- ✅ Comprehensive test infrastructure (280+ tests, 94% coverage)
- ✅ GitHub Actions CI/CD (automated testing, security scanning, Docker builds)
- ✅ Health check endpoints (basic + orchestration probes)
- ✅ Frontend SvelteKit application with TypeScript
- ✅ Frontend UI components (Button, Modal, Toast, LoadingSpinner, etc.)
- ✅ Story management features (metadata, tags, templates, cloning, archiving, statistics)
- ✅ Beat features (reordering, modification, insertion, coherence checking)
- ✅ Story authoring modes (Autonomous/Collaborative/Manual)
- ✅ World event timeline and story intersection views
- ✅ MIT License

## Quick Start for New Contributors

1. Clone repository and install dependencies
2. Start Docker services: `docker-compose -f docker/docker-compose.yml up`
3. Run migrations: `docker exec shinkei-backend poetry run alembic upgrade head`
4. Access API docs: http://localhost:8000/api/v1/docs
5. Access frontend: http://localhost:5173
6. Check health: `curl http://localhost:8000/health`
7. Run tests: `cd backend && poetry run pytest`
8. View CI/CD workflows: See `.github/workflows/README.md`

## License

This project is licensed under the **MIT License**.

Copyright (c) 2025 SHINKEI Project

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

See the [LICENSE](LICENSE) file for full details.
