# Docker Guide - AI Inkubator

## Project Structure

The Docker-related files are organized in the `docker/` folder:

```
ai-inkubator/
├── docker/
│   ├── Dockerfile              # Multi-stage build for backend
│   ├── .dockerignore           # Build context exclusions
│   ├── README.md               # Docker documentation
│   └── scripts/
│       ├── start.bat           # Quick start (Windows)
│       ├── start.sh            # Quick start (Linux/Mac)
│       ├── stop.bat            # Quick stop (Windows)
│       ├── stop.sh             # Quick stop (Linux/Mac)
│       ├── entrypoint.sh       # Container entrypoint
│       └── wait-for-db.sh      # Database readiness check
├── docker-compose.yaml         # Multi-service orchestration (kept in root)
├── docker-start.bat            # Root wrapper (calls docker/scripts/start.bat)
├── docker-start.sh             # Root wrapper (calls docker/scripts/start.sh)
├── docker-stop.bat             # Root wrapper (calls docker/scripts/stop.bat)
└── docker-stop.sh              # Root wrapper (calls docker/scripts/stop.sh)
```

## Quick Start

### Windows

```cmd
docker-start.bat
```

Or directly:

```cmd
docker\scripts\start.bat
```

### Linux/Mac

```bash
./docker-start.sh
```

Or directly:

```bash
./docker/scripts/start.sh
```

## Services

The Docker Compose setup includes three services:

### 1. Backend (`backend`)

- **Image**: Built from `docker/Dockerfile`
- **Port**: 8000
- **Health Check**: GET /health endpoint
- **Environment**: Loaded from `.env`
- **Dependencies**: Waits for MySQL database to be healthy

### 2. MySQL Database (`db`)

- **Image**: `mysql:8.0`
- **Port**: 3306 (not exposed to host)
- **Health Check**: `mysqladmin ping`
- **Data**: Persisted in `mysql_data` volume
- **Environment**:
  - `MYSQL_ROOT_PASSWORD`: root
  - `MYSQL_DATABASE`: ai_inkubator_db
  - `MYSQL_USER`: ai_inkubator_user
  - `MYSQL_PASSWORD`: ai_inkubator_pass

### 3. phpMyAdmin (`phpmyadmin`)

- **Image**: `phpmyadmin:latest`
- **Port**: 8081
- **Purpose**: Web-based MySQL administration
- **Access**: http://localhost:8081
- **Credentials**: Use MySQL user credentials above

## Service URLs

| Service    | URL                          | Description           |
| ---------- | ---------------------------- | --------------------- |
| Backend    | http://localhost:8000        | API endpoints         |
| API Docs   | http://localhost:8000/docs   | Swagger UI            |
| phpMyAdmin | http://localhost:8081        | Database admin panel  |
| Health     | http://localhost:8000/health | Service health status |

## Common Commands

### Start Services

```bash
# Build and start in detached mode
docker-compose up -d --build

# Start without rebuilding
docker-compose up -d

# Start and view logs
docker-compose up --build
```

### Stop Services

```bash
# Stop containers (keep volumes)
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Database only
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100 -f backend
```

### Rebuild Services

```bash
# Rebuild specific service
docker-compose build backend

# Rebuild without cache
docker-compose build --no-cache backend
```

### Execute Commands in Container

```bash
# Open bash in backend container
docker-compose exec backend bash

# Run database migrations
docker-compose exec backend uv run alembic upgrade head

# Access MySQL CLI
docker-compose exec db mysql -u ai_inkubator_user -p ai_inkubator_db
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### View Service Status

```bash
docker-compose ps
```

## Dockerfile Details

The `docker/Dockerfile` uses a multi-stage build:

### Stage 1: Builder

- Base: `python:3.12-slim`
- Installs `uv` for fast dependency management
- Copies `pyproject.toml` and `uv.lock`
- Runs `uv sync --frozen --no-dev` for reproducible builds

### Stage 2: Runtime

- Base: `python:3.12-slim`
- Copies virtual environment from builder
- Copies application code
- Installs `curl` for health checks
- Exposes port 8000
- Command: `uv run fastapi run --host 0.0.0.0 --port 8000`

## Environment Variables

Required environment variables in `.env`:

```env
# Application
APP_NAME=AI Inkubator
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database (must match docker-compose.yaml)
DATABASE_URL=mysql+pymysql://ai_inkubator_user:ai_inkubator_pass@db:3306/ai_inkubator_db

# Firebase
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_PROJECT_ID=your-project-id

# Security
SECRET_KEY=your-secret-key-here
```

**Important**: In `DATABASE_URL`, use `@db:3306` (service name) instead of `@localhost:3306`

## Volumes

### `mysql_data`

- Purpose: Persist MySQL database files
- Location: Docker-managed volume
- Remove: `docker-compose down -v`

## Networking

All services are on the same Docker network:

- Backend connects to database via service name `db`
- phpMyAdmin connects to database via service name `db`
- Ports 8000 and 8081 are exposed to host

## Troubleshooting

### Backend crashes on startup

**Problem**: Database not ready when backend starts

**Solution**: The `docker/scripts/wait-for-db.sh` script handles this automatically. If issues persist, check database logs:

```bash
docker-compose logs db
```

### Permission denied errors

**Problem**: Shell scripts not executable

**Solution**:

```bash
chmod +x docker-start.sh docker-stop.sh
chmod +x docker/scripts/*.sh
```

### Port already in use

**Problem**: Port 8000 or 8081 already in use

**Solution**:

```bash
# Find process using port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Stop the process or change port in docker-compose.yaml
```

### Can't connect to database

**Problem**: Backend can't reach MySQL

**Solution**:

1. Ensure DATABASE_URL uses `@db:3306` (service name)
2. Check if database is healthy: `docker-compose ps`
3. Verify network: `docker network inspect ai-inkubator_default`

### Firebase credentials not found

**Problem**: Backend can't find `firebase-credentials.json`

**Solution**:

1. Copy Firebase credentials to project root
2. Ensure `.env` has correct path: `FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json`
3. Rebuild: `docker-compose up -d --build`

### Changes not reflected in container

**Problem**: Code changes don't appear after rebuild

**Solution**:

```bash
# Full rebuild without cache
docker-compose build --no-cache backend
docker-compose up -d

# Or remove image and rebuild
docker-compose down
docker rmi ai-inkubator-backend
docker-compose up -d --build
```

## Development Workflow

### Local Development (without Docker)

```bash
# Install dependencies
uv sync --dev

# Run development server
uv run fastapi dev

# Run tests
uv run pytest
```

### Production Deployment (with Docker)

```bash
# Build and start services
docker-compose up -d --build

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Docker Build

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker-compose build backend

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: sleep 10

      - name: Health check
        run: curl --fail http://localhost:8000/health

      - name: Stop services
        run: docker-compose down
```

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [uv Documentation](https://github.com/astral-sh/uv)

## See Also

- [README.md](README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing authentication
- [docker/README.md](docker/README.md) - Docker folder structure
