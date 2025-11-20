# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the Shinkei project.

## Workflows

### 1. CI (`ci.yml`)

**Purpose**: Automated testing and code quality checks

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs**:

#### Backend Job
- Sets up Python 3.11 environment
- Installs dependencies via Poetry
- Runs code formatter check (Black)
- Runs linter (Ruff)
- Runs type checker (Mypy)
- Executes full test suite with coverage
- Uploads coverage to Codecov

**Services**: PostgreSQL 16 (for integration tests)

#### Frontend Job
- Sets up Node.js 20 environment
- Installs dependencies via npm
- Runs linter (ESLint)
- Runs type checker (SvelteKit check)
- Runs tests (Vitest)
- Builds production bundle

#### Integration Job
- Runs after backend and frontend jobs
- Applies Alembic migrations
- Executes integration test suite
- Verifies end-to-end functionality

**Environment Variables Required**:
- `DATABASE_URL`: PostgreSQL connection string (provided by service)
- `ENVIRONMENT`: Set to `testing`
- `SECRET_KEY`: Test secret key
- `SUPABASE_URL`: Mock Supabase URL
- `SUPABASE_KEY`: Mock Supabase key

---

### 2. Security Scan (`security-scan.yml`)

**Purpose**: Automated security vulnerability scanning

**Triggers**:
- Push to `main` branch
- Pull requests to `main`
- Weekly schedule (Mondays at 00:00 UTC)
- Manual trigger via workflow_dispatch

**Jobs**:

#### Trivy Scan
- Scans entire filesystem for vulnerabilities
- Generates SARIF report for GitHub Security
- Uploads findings to Security tab
- Fails on CRITICAL or HIGH severity issues

#### Python Security
- Runs Bandit security linter on Python code
- Runs Safety to check for known vulnerabilities in dependencies
- Uploads security reports as artifacts

#### Docker Security
- Builds Docker images for backend and frontend
- Scans images with Trivy for OS and library vulnerabilities
- Reports findings (non-blocking initially)

**Permissions Required**:
- `contents: read` - Read repository code
- `security-events: write` - Upload to GitHub Security

---

### 3. Docker Build (`docker-build.yml`)

**Purpose**: Verify Docker images build successfully

**Triggers**:
- Push to `main` or `develop` (when Docker-related files change)
- Pull requests (when Docker-related files change)

**Path Filters**:
- `docker/**`
- `backend/**`
- `frontend/**`

**Jobs**:

#### Build Backend
- Uses Docker Buildx for efficient builds
- Builds backend image from `docker/Dockerfile.backend`
- Caches layers in GitHub Actions cache
- Verifies image was created successfully
- Tests that container can start

#### Build Frontend
- Builds frontend image from `docker/Dockerfile.frontend`
- Caches layers for faster subsequent builds
- Verifies image creation
- Tests container startup

#### Docker Compose Test
- Starts full stack with `docker-compose up`
- Waits for services to initialize
- Checks service health
- Tests backend health endpoint
- Tests frontend accessibility
- Cleans up containers and volumes

---

## Monitoring

### CI Status Badges

Add these to your README.md:

```markdown
![CI](https://github.com/YOUR_USERNAME/SHINKEI/workflows/CI/badge.svg)
![Security Scan](https://github.com/YOUR_USERNAME/SHINKEI/workflows/Security%20Scan/badge.svg)
![Docker Build](https://github.com/YOUR_USERNAME/SHINKEI/workflows/Docker%20Build%20Verification/badge.svg)
```

### View Workflow Runs

- **CI Results**: https://github.com/YOUR_USERNAME/SHINKEI/actions?query=workflow%3ACI
- **Security Scans**: https://github.com/YOUR_USERNAME/SHINKEI/security/code-scanning
- **Docker Builds**: https://github.com/YOUR_USERNAME/SHINKEI/actions?query=workflow%3A%22Docker+Build%22

---

## Troubleshooting

### Common Issues

**Problem**: Backend tests fail with database connection error
- **Solution**: Check PostgreSQL service is healthy in workflow logs
- Verify `DATABASE_URL` environment variable is set correctly

**Problem**: Coverage upload fails
- **Solution**: Codecov token may need to be configured in repository secrets
- Add `CODECOV_TOKEN` to GitHub Secrets if using private repository

**Problem**: Security scan finds vulnerabilities
- **Solution**: Review findings in GitHub Security tab
- Update dependencies to patched versions
- Add false positives to `.trivyignore` if necessary

**Problem**: Docker build fails
- **Solution**: Check Dockerfile syntax
- Verify all `COPY` paths exist
- Test build locally with `docker build -f docker/Dockerfile.backend ./backend`

**Problem**: Frontend build hangs
- **Solution**: May need to increase Node memory
- Add `NODE_OPTIONS=--max_old_space_size=4096` to environment

---

## Local Testing

### Run CI Checks Locally

**Backend**:
```bash
cd backend
poetry run black --check .
poetry run ruff check .
poetry run mypy src/
poetry run pytest -v --cov
```

**Frontend**:
```bash
cd frontend
npm run lint
npm run check
npm test
npm run build
```

### Run Security Scans Locally

**Trivy**:
```bash
# Install Trivy
brew install aquasecurity/trivy/trivy  # macOS
# or
sudo apt-get install trivy  # Linux

# Scan filesystem
trivy fs .

# Scan Docker image
docker build -t shinkei-backend:test -f docker/Dockerfile.backend ./backend
trivy image shinkei-backend:test
```

**Bandit**:
```bash
cd backend
poetry run bandit -r src/
```

**Safety**:
```bash
cd backend
poetry run safety check
```

### Test Docker Builds Locally

```bash
# Backend
docker build -f docker/Dockerfile.backend -t shinkei-backend:local ./backend

# Frontend
docker build -f docker/Dockerfile.frontend -t shinkei-frontend:local ./frontend

# Full stack
cd docker
docker-compose up
```

---

## Optimization Tips

### Speed Up Workflows

1. **Cache Dependencies**
   - Poetry: Uses `cache: 'pip'` in setup-python
   - npm: Uses `cache: 'npm'` in setup-node
   - Docker: Uses GitHub Actions cache

2. **Parallel Jobs**
   - Backend and Frontend jobs run in parallel
   - Use matrix strategy for testing multiple Python/Node versions (if needed)

3. **Skip Unnecessary Runs**
   - Use path filters to run only when relevant files change
   - Use `if` conditions to skip jobs based on commit message

### Reduce GitHub Actions Minutes

- Set `continue-on-error: true` for non-critical checks
- Use self-hosted runners for private projects (if available)
- Cache aggressively to reduce build times

---

## Maintenance

### Weekly Tasks
- Review security scan results
- Update dependency versions
- Check for workflow action updates

### Monthly Tasks
- Review and update workflow configurations
- Optimize caching strategies
- Update documentation

---

## Contributing

When adding new workflows:
1. Test locally first
2. Document purpose and triggers
3. Add to this README
4. Set appropriate permissions
5. Use semantic job names
6. Include error handling
