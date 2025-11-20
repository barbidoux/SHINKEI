# ♊ GEMINI.md - Shinkei Project Context

## 1. Project Overview
**Shinkei (心継)** is a narrative engine for generating, co-authoring, and manually writing interconnected inner worlds.
- **Core Concept**: Users create "Worlds" with "Stories" made of "StoryBeats".
- **Unique Feature**: Global timeline where stories intersect via shared "WorldEvents".
- **Modes**: Autonomous (AI), Collaborative (Hybrid), Manual.

## 2. Architecture & Tech Stack
- **Pattern**: Modular Monolith (Domain-driven modules in a single deployable unit).
- **Backend**: FastAPI (Python 3.11+), SQLModel, Pydantic.
- **Frontend**: SvelteKit (Node 20+), TailwindCSS, Bits UI.
- **Database**: Supabase (PostgreSQL) - Local via Docker, Prod via Cloud.
- **AI**: Abstracted `NarrativeModel` interface (OpenAI, Anthropic, Local).
- **Observability**: OpenTelemetry + SigNoz.

## 3. Project Structure
```
shinkei/
├── backend/            # FastAPI Modular Monolith
│   ├── src/shinkei/    # Application Code
│   │   ├── auth/       # AuthN/AuthZ
│   │   ├── worlds/     # World Management
│   │   ├── stories/    # Story Management
│   │   ├── generation/ # AI Engine
│   │   └── main.py     # App Entrypoint
│   └── tests/          # Pytest Suite
├── frontend/           # SvelteKit App
│   └── src/routes/     # File-based Routing
└── docker/             # Docker Compose Setup
```

## 4. Key Development Commands
### Backend
- **Run Dev**: `docker-compose up backend`
- **Tests**: `cd backend && poetry run pytest`
- **Lint**: `poetry run ruff check .`
- **Format**: `poetry run black .`
- **Migrations**: `poetry run alembic upgrade head`

### Frontend
- **Run Dev**: `npm run dev`
- **Tests**: `npm test`
- **Check**: `npm run check`

## 5. Critical Implementation Rules
1.  **Modular Monolith**: No cross-module DB joins. Use internal API facades.
2.  **Security**:
    -   Auth via Supabase (JWT).
    -   Stateless Backend (Local JWT validation).
    -   Explicit Ownership Checks (`verify_world_ownership`).
3.  **Database**:
    -   "Expand and Contract" migration strategy.
    -   GraphRAG-ready schema (Adjacency Lists for entities).
4.  **AI Integration**:
    -   Always use `NarrativeModel` interface.
    -   Never hardcode provider logic in business layers.

## 6. Documentation Map
- **Specs**: `SHINKEI_SPECS.md`
- **Architecture**: `Shinkei (心継) Project_ Software Architecture Document.md`
- **Plan**: `IMPLEMENTATION_PLAN/SHINKEI_IMPLEMENTATION_PLAN.md`
- **AI Guide**: `IMPLEMENTATION_PLAN/SHINKEI_AI_ENGINE_FRONTEND_GUIDE.md`
- **Quick Start**: `IMPLEMENTATION_PLAN/SHINKEI_QUICK_START_GUIDE.md`
