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
      └── /api (app/api/router.py)
          └── /auth (app/api/routes/auth_route.py)
```

**Adding new routes:**

1. Create route file in `app/api/routes/` (e.g., `my_route.py`)
2. Import and include in `app/api/router.py` using `api_router.include_router(my_route.router)`
3. Routes automatically get `/api` prefix

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

- Pydantic models for request/response DTOs in `app/models/dto/` (e.g., `auth_dto.py`, `user_dto.py`)
- SQLAlchemy ORM models for database tables (e.g., `user_model.py`)
- `app/models/__init__.py` centralizes all model imports for SQLAlchemy metadata registration
- Domain models/dataclasses

### Logging

- Import logger: `import logging; logger = logging.getLogger(__name__)`
- Log level controlled by `LOG_LEVEL` env var
- Request timing is automatically logged by middleware (see `server.py:add_timing`)

## Key Files Reference

| File                           | Purpose                                                       |
| ------------------------------ | ------------------------------------------------------------- |
| `app/core/server.py`           | Application factory, middleware setup, root routes            |
| `app/core/config.py`           | Centralized configuration (Settings class)                    |
| `app/core/schema.py`           | Standard response schemas and helper functions                |
| `app/core/database.py`         | SQLAlchemy engine, session management, database init          |
| `app/core/security.py`         | Firebase authentication, JWT verification, dependencies       |
| `app/api/router.py`            | API route aggregator (includes all route modules)             |
| `app/api/health_route.py`      | Health check endpoint                                         |
| `app/api/routes/auth_route.py` | Authentication routes (login, profile, update, deactivate)    |
| `app/models/__init__.py`       | Model registration for SQLAlchemy metadata                    |
| `app/models/user_model.py`     | User ORM model with short ID, role, and Firebase integration  |
| `app/models/dto/auth_dto.py`   | Authentication request/response DTOs (Pydantic)               |
| `app/services/auth_service.py` | Auth business logic with short ID generation                  |
| `app/services/health.py`       | Health check service                                          |
| `alembic.ini`                  | Alembic configuration for database migrations                 |
| `alembic/env.py`               | Alembic environment setup with auto-discovery                 |
| `alembic/versions/`            | Migration history (4 migrations: initial, UUID, role changes) |
| `pyproject.toml`               | Dependencies and project metadata (managed by uv)             |
| `firebase-credentials.json`    | Firebase service account credentials (gitignored)             |
| `docs/QUICKSTART.md`           | Quick start guide for getting started                         |
| `docs/MIGRATION_GUIDE.md`      | Database migrations guide with Alembic                        |
| `docs/SETUP_AUTH.md`           | Firebase authentication setup guide                           |

## Common Tasks

**Add a new API endpoint:**

1. Create `app/api/routes/feature_route.py` with router
2. Include in `app/api/router.py`: `api_router.include_router(feature_route.router)`
3. Use `BaseResponse` model and `create_success_response()` helper

**Add a new database model:**

1. Create SQLAlchemy model in `app/models/feature_model.py`
2. Import in `app/models/__init__.py` to register with Base.metadata
3. Create Pydantic DTOs in `app/models/dto/feature_dto.py`
4. Generate migration: `uv run alembic revision --autogenerate -m "Add feature table"`
5. Review generated migration in `alembic/versions/`
6. Apply migration: `uv run alembic upgrade head`

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
3. Send to backend: `POST /api/auth/login` with `{"firebase_token": token}`
4. Store user info from response
5. For protected endpoints, include: `Authorization: Bearer <token>`

**Backend protected route:**

```python
from app.core.security import get_current_user_firebase_uid
from app.core.database import get_db
from app.models.user_model import User
from sqlalchemy.orm import Session

@router.get("/protected")
async def protected(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    # ... use user data
```

**Available auth endpoints:**

- `POST /api/auth/login` - Login/register with Firebase token
- `GET /api/auth/me` - Get current user profile (protected)
- `PUT /api/auth/me` - Update profile (protected)
- `DELETE /api/auth/me` - Deactivate account (protected)

**Dependencies for protected routes:**

```python
from app.core.security import get_current_user_firebase_uid
from app.core.database import get_db
from sqlalchemy.orm import Session

@router.get("/protected")
async def protected_endpoint(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db)
):
    # firebase_uid is verified, query user from database
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    return create_success_response(data={"user_id": user.id})
```

## Database Setup

### First-Time Setup (Clone Project)

1. **Create MySQL database:**

   ```sql
   CREATE DATABASE ai_inkubator CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. **Configure environment:**

   ```bash
   # Copy .env.example to .env
   cp .env.example .env

   # Update DATABASE_URL in .env
   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/ai_inkubator
   ```

3. **Install dependencies:**

   ```bash
   uv sync
   ```

4. **Apply migrations:**

   ```bash
   # Apply all existing migrations
   uv run alembic upgrade head

   # Verify current migration
   uv run alembic current
   ```

5. **Run application:**
   ```bash
   uv run fastapi dev
   ```

### Database Migrations with Alembic

**Project uses Alembic for version-controlled schema changes.**

**Creating new migrations:**

```bash
# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "Add new table"

# Review generated migration file in alembic/versions/
# Edit if needed (Alembic doesn't catch everything)

# Apply migration
uv run alembic upgrade head
```

**Common Alembic commands:**

```bash
# Check current migration status
uv run alembic current

# View migration history
uv run alembic history --verbose

# Rollback last migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade <revision_id>

# Create empty migration (for data migrations)
uv run alembic revision -m "Custom data migration"
```

**Important notes:**

- Always import new models in `app/models/__init__.py` before running `--autogenerate`
- Review generated migrations - Alembic doesn't detect all changes (indexes, constraints)
- Test migrations on dev database before production
- Commit migration files to version control
- See `docs/MIGRATION_GUIDE.md` for detailed guide
- See `alembic/README.md` for comprehensive documentation

### Database Model Pattern

**User model structure (app/models/user_model.py):**

- `id` (CHAR(4), primary key) - Short 4-character random ID (e.g., "A1B2"), generated using `auth_service.generate_short_id()`
- `firebase_uid` (String(128), unique, indexed) - Links to Firebase Auth
- `email` (String(255), unique, indexed)
- `display_name`, `photo_url`, `phone_number` (optional metadata)
- `role` (Enum: UserRole) - User role: `admin`, `tenant`, or `guest` (default)
- `is_active` (Boolean, default=True) - Soft delete flag
- `email_verified` (Boolean, default=False)
- `created_at`, `updated_at` (DateTime with timezone)
- `last_login` (DateTime, nullable)

**User Role System:**

The project implements a three-tier role system (UserRole enum in user_model.py):

- `ADMIN` - Full system access, can approve tenant requests
- `TENANT` - Approved user with full application access
- `GUEST` - Default role after registration, limited access (awaiting approval)

New users are automatically assigned the `guest` role upon registration. Admins can promote users to `tenant` status.

**Short ID System:**

User IDs use a compact 4-character format (A-Z, 0-9) for:

- Human-readable identifiers in UI
- QR codes and compact displays
- Easy reference in support tickets

Generated via `auth_service.generate_short_id()` using cryptographically secure random generation (36^4 = 1,679,616 combinations).

**When adding new models:**

1. Inherit from `Base` (from `app.core.database`)
2. Use `__tablename__` for explicit table name
3. Add `__table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}` for MySQL compatibility
4. Include `created_at` and `updated_at` timestamp columns
5. Add indexes on frequently queried columns
6. Import in `app/models/__init__.py` for metadata registration
7. Include `to_dict()` method for easy serialization
