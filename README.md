# Shinkei (心継) - Narrative Engine

A narrative engine for generating, co-authoring, and manually writing interconnected inner worlds. Create self-contained narrative universes with stories that can intersect through shared world events on a global timeline.

## Overview

**Shinkei** enables users to:
- Create **Worlds** with customizable tone, laws, and chronology modes
- Write **Stories** in three authoring modes (Autonomous AI, Collaborative, Manual)
- Generate **Story Beats** using multiple LLM providers
- Define **World Events** on a canonical timeline where stories intersect
- Manage all entities through a professional, type-safe web interface

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL via SQLAlchemy 2.0
- **Migrations**: Alembic
- **Auth**: Supabase (JWT-based)
- **Testing**: Pytest with pytest-asyncio

### Frontend
- **Framework**: SvelteKit 2.x (Node 20+)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Components**: Custom component library
- **Auth**: Supabase client

### Infrastructure
- **Development**: Docker Compose
- **Database**: Supabase PostgreSQL
- **LLM Providers**: OpenAI, Anthropic, Ollama (local/remote)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd SHINKEI

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit .env files with your credentials
# - SUPABASE_URL and SUPABASE_KEY
# - DATABASE_URL
# - OpenAI/Anthropic API keys (optional)
```

### 2. Start with Docker Compose

```bash
# Start all services (PostgreSQL, Backend, Frontend)
docker-compose -f docker/docker-compose.yml up

# In separate terminal: Run database migrations
docker exec shinkei-backend poetry run alembic upgrade head
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs

## Features

### Three Authoring Modes

1. **Autonomous Mode**
   - AI generates story beats automatically
   - Full control handed to the LLM
   - Fastest way to generate narrative content

2. **Collaborative Mode**
   - AI proposes content
   - User reviews and edits before accepting
   - Perfect balance of AI assistance and human creativity

3. **Manual Mode**
   - User writes content manually
   - AI can provide suggestions and assistance
   - Full creative control

### LLM Provider Support

- **OpenAI**: GPT-4o and other models
- **Anthropic**: Claude 3.5 Sonnet
- **Ollama**: Local or remote models with custom host URL
  - Perfect for running models on Windows servers or separate machines
  - Configure custom host in Settings (e.g., `http://192.168.1.100:11434`)

### Complete Data Model

```
User
  └── World (tone, laws, backdrop, chronology_mode)
      ├── WorldEvent (t, label_time, location, type, summary)
      └── Story (title, synopsis, mode, pov_type)
          └── StoryBeat (content, type, order_index, world_event_id)
```

### World Events Timeline

- Create canonical events with objective time values (`t`)
- Add human-readable labels ("Year 2145", "The Great War")
- Link story beats to events for narrative intersection
- Stories naturally converge at shared timeline events

## Development

### Backend Development

```bash
cd backend

# Install dependencies
poetry install

# Run migrations
poetry run alembic upgrade head

# Start dev server
poetry run uvicorn src.shinkei.main:app --reload

# Run tests
poetry run pytest
poetry run pytest --cov

# Code quality
poetry run black .
poetry run ruff check .
poetry run mypy src/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Type checking
npm run check

# Lint & format
npm run lint
npm run format

# Run tests
npm test
```

### Database Migrations

```bash
cd backend

# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

## Project Structure

```
shinkei/
├── backend/
│   ├── src/shinkei/
│   │   ├── api/v1/           # API endpoints
│   │   ├── auth/             # Authentication
│   │   ├── database/         # DB setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── repositories/     # Data access layer
│   │   ├── schemas/          # Pydantic schemas
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Migrations
│   └── tests/                # Tests
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/   # Reusable components
│   │   │   ├── stores/       # Svelte stores
│   │   │   └── types/        # TypeScript types
│   │   └── routes/           # SvelteKit pages
│   └── package.json
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
└── IMPLEMENTATION_PLAN/      # Detailed guides
```

## Frontend Components

### Reusable Component Library

- **Button**: Primary, secondary, danger, ghost variants with loading states
- **Modal**: Confirmation dialogs with danger/primary variants
- **Toast**: Success/error/info/warning notifications
- **LoadingSpinner**: Configurable sizes with optional text
- **Breadcrumb**: Navigation breadcrumbs
- **EmptyState**: Illustrated empty states for better UX
- **GenerationPanel**: AI beat generation with provider selection

### Usage Example

```svelte
<script>
  import { Button, Modal, LoadingSpinner } from '$lib/components';
</script>

<Button variant="primary" loading={isLoading}>
  Save Changes
</Button>

<LoadingSpinner size="lg" text="Loading data..." />
```

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /users/me` - Current user info
- `PUT /users/me` - Update user settings

### Worlds
- `GET /worlds` - List user's worlds
- `POST /worlds` - Create world
- `GET /worlds/{id}` - Get world details
- `PUT /worlds/{id}` - Update world
- `DELETE /worlds/{id}` - Delete world

### Stories
- `GET /worlds/{id}/stories` - List world's stories
- `POST /worlds/{id}/stories` - Create story
- `GET /stories/{id}` - Get story details
- `DELETE /stories/{id}` - Delete story

### Story Beats
- `GET /stories/{id}/beats` - List story beats
- `POST /stories/{id}/beats` - Create beat manually
- `PUT /stories/{id}/beats/{beat_id}` - Update beat
- `DELETE /stories/{id}/beats/{beat_id}` - Delete beat
- `POST /narrative/stories/{id}/beats/generate` - Generate beat with AI

### World Events
- `GET /worlds/{id}/events` - List world events
- `POST /worlds/{id}/events` - Create event
- `GET /worlds/{id}/events/{event_id}` - Get event
- `PUT /worlds/{id}/events/{event_id}` - Update event
- `DELETE /worlds/{id}/events/{event_id}` - Delete event

## Configuration

### Backend (.env)

```env
DATABASE_URL=postgresql://user:password@localhost:5432/shinkei
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
```

### Frontend (.env)

```env
PUBLIC_SUPABASE_URL=https://your-project.supabase.co
PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
PUBLIC_API_URL=http://localhost:8000
```

## User Settings

Configure your preferred LLM provider in Settings:

1. **Provider**: OpenAI, Anthropic, or Ollama
2. **Model**: Select or specify custom model
3. **Ollama Host**: For remote Ollama servers (e.g., Windows PC)
4. **UI Theme**: Light, dark, or system
5. **Language**: Preferred language

## Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in backend .env
- [ ] Use strong `SECRET_KEY`
- [ ] Configure CORS origins properly
- [ ] Set up PostgreSQL backup strategy
- [ ] Configure Supabase for production
- [ ] Set up API keys for LLM providers
- [ ] Enable HTTPS
- [ ] Configure logging and monitoring

### Docker Production Build

```bash
# Build production images
docker-compose -f docker/docker-compose.yml build

# Start in production mode
docker-compose -f docker/docker-compose.yml up -d

# Check logs
docker-compose -f docker/docker-compose.yml logs -f
```

## Testing

### Run All Tests

```bash
# Backend tests
cd backend
poetry run pytest --cov

# Frontend tests
cd frontend
npm test
```

### Test Coverage

The backend test suite includes:
- Unit tests for repositories and services
- Integration tests with database
- API endpoint tests
- Target: 80%+ coverage

## Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Verify DATABASE_URL in .env
# Run migrations
poetry run alembic upgrade head
```

**Frontend Build Errors**
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear SvelteKit cache
rm -rf .svelte-kit
```

**Ollama Connection Issues**
- Ensure Ollama server is running
- Check firewall allows connections on port 11434
- Verify host URL in Settings (must include http://)
- Test connection: `curl http://your-ollama-host:11434/api/tags`

## Documentation

- **[SHINKEI_SPECS.md](SHINKEI_SPECS.md)**: Complete specification
- **[CLAUDE.md](CLAUDE.md)**: Quick reference guide
- **[IMPLEMENTATION_PLAN/](IMPLEMENTATION_PLAN/)**: Detailed implementation guides

## Contributing

1. Follow the code style (Black for Python, Prettier for TypeScript)
2. Write tests for new features
3. Update documentation
4. Create descriptive commit messages
5. Use feature branches

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository-issues-url]
- Documentation: [docs-url]
- Email: [support-email]

---

**Shinkei (心継)** - Connecting narrative threads across inner worlds.
