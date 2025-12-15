# Copilot Instructions for ai-inkubator

## Project Overview

This is a **FastAPI-based AI service** using **uv** for dependency management. The application follows a layered architecture with clear separation between API routes, business logic, and ML components. Authentication is handled via **Firebase Auth** with user data stored in **MySQL using SQLAlchemy**.

## Architecture Pattern

### Application Factory Pattern

- `app/main.py` exports the app instance created by `app/core/server.py:create_application()`
- All middleware, routes, and configuration are wired up in `create_application()`
- Never create FastAPI instances elsewhere; always use the factory

### Routing Hierarchy

```
app/main.py (entry)
  └── app/core/server.py (factory)
      ├── / (index route - inline in server.py)
      ├── /health (app/api/health_route.py)
      └── /api/v1 (app/api/v1/router.py)
          ├── /ping (app/api/v1/routes/ping_route.py)
          └── /auth (app/api/v1/routes/auth_route.py)
```

**Adding new routes:**

1. Create route file in `app/api/v1/routes/` (e.g., `my_route.py`)
2. Import and include in `app/api/v1/router.py` using `router_v1.include_router(my_route.router)`
3. Routes automatically get `/api/v1` prefix and `["v1"]` tag

### Response Schema Pattern

**Always use standardized responses** from `app/core/schema.py`:

```python
from app.core.schema import BaseResponse, create_success_response, create_error_response

@router.get("/endpoint", response_model=BaseResponse)
async def endpoint():
    return create_success_response(message="Success", data={"key": "value"})
```

Response structure:

```json
{
  "status": "success|failed|error|warning",
  "message": "Human-readable message",
  "data": null | any
}
```

### Configuration Management

- All config in `app/core/config.py` using Pydantic Settings
- Environment variables loaded via `python-dotenv` from `.env` file
- Access config globally: `from app.core.config import settings`
- Use `settings.is_production` or `settings.is_development` for environment checks
- Config fields use `os.getenv()` - ensure `.env` has all vars from `.env.example`

### Service Layer Pattern

Business logic goes in `app/services/`:

```python
# app/services/my_service.py
def my_business_logic() -> BaseResponse:
    # Complex logic here
    return create_success_response(...)

# app/api/v1/routes/my_route.py
from app.services.my_service import my_business_logic

@router.get("/")
async def endpoint():
    return my_business_logic()
```

## Development Workflow

### Running the Application

```bash
# Development with hot reload
uv run fastapi dev

# Production mode
uv run fastapi run
```

### Dependency Management

```bash
# Install dependencies (from pyproject.toml)
uv sync

# Install with dev dependencies (pytest, ruff, httpx)
uv sync --dev

# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev package-name
```

### Docker

```bash
# Build image
docker build -t fastapi-uv-backend .

# Run container
docker run -p 8000:8000 --env-file .env fastapi-uv-backend
```

**Important**: Dockerfile uses multi-stage build with `uv sync --frozen --no-dev` to ensure reproducible builds

## Project-Specific Conventions

### Middleware Order Matters

In `app/core/server.py`, middlewares are applied in reverse order:

1. Security headers middleware (runs last)
2. Timing middleware (logs request duration with `X-Process-Time` header)
3. TrustedHostMiddleware (production only)
4. CORSMiddleware (runs first)

### ML Components

- ML models stored in path from `settings.ml_models_path` env var
- `app/ml/` is structured for inference logic, models, and preprocessing
- Currently placeholder - when implementing ML features, follow this structure

### Models Directory

`app/models/` is for **data models** (DTOs, ORM models), NOT ML models:

- Pydantic models for request/response DTOs (e.g., `auth_dto.py`)
- SQLAlchemy models for database tables (e.g., `user.py`)
- Domain models/dataclasses

### Logging

- Import logger: `import logging; logger = logging.getLogger(__name__)`
- Log level controlled by `LOG_LEVEL` env var
- Request timing is automatically logged by middleware (see `server.py:add_timing`)

## Key Files Reference

| File                   | Purpose                                            |
| ---------------------- | -------------------------------------------------- |
| `app/core/server.py`   | Application factory, middleware setup, root routes |
| `app/core/config.py`   | Centralized configuration (Settings class)         |
| `app/core/schema.py`   | Standard response schemas and helper functions     |
| `app/api/v1/router.py` | V1 API route aggregator                            |
| `pyproject.toml`       | Dependencies and project metadata (managed by uv)  |

## Common Tasks

**Add a new API endpoint:**

1. Create `app/api/v1/routes/feature_route.py` with router
2. Include in `app/api/v1/router.py`: `router_v1.include_router(feature_route.router)`
3. Use `BaseResponse` model and `create_success_response()` helper

**Add environment variable:**

1. Add to `.env.example` and `.env`
2. Add field to `Settings` class in `app/core/config.py`
3. Access via `settings.variable_name`

**Add middleware:**
Add in `app/core/server.py:setup_middlewares()` using `app.add_middleware()` or `@app.middleware("http")` decorator

## Authentication Workflow

**Client-side authentication:**

1. User signs in with Firebase (Google, Email/Password, etc.)
2. Get ID token: `const token = await user.getIdToken()`
3. Send to backend: `POST /api/v1/auth/login` with `{"firebase_token": token}`
4. Store user info from response
5. For protected endpoints, include: `Authorization: Bearer <token>`

**Backend protected route:**

```python
@router.get("/protected")
async def protected(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    # ... use user
```

**Available auth endpoints:**

- `POST /api/v1/auth/login` - Login/register with Firebase token
- `GET /api/v1/auth/me` - Get current user profile (protected)
- `PUT /api/v1/auth/me` - Update profile (protected)
- `DELETE /api/v1/auth/me` - Deactivate account (protected)

## Database Setup

**Required steps before first run:**

1. Create MySQL database
2. Update `.env` with connection string: `DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname`
3. Tables auto-created on startup via `init_db()` in lifespan manager
4. User model has Firebase UID as unique identifier mapping to Firebase Auth

**Migration pattern (if needed):**

- Currently using `Base.metadata.create_all()` for simple table creation
- For production, consider adding Alembic for migrations
