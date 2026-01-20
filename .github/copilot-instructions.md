# Copilot Instructions for ai-sims (AI Incubator Management System)

## Project Overview

A **FastAPI-based AI-powered incubator management system** using **uv** for dependency management. Manages tenant registrations, business proposals, and AI-driven proposal classification using fine-tuned IndoBERT. Architecture follows a clean layered pattern with **repositories**, **services**, and **API routes**. Authentication via **Firebase Auth**, data persistence in **MySQL/SQLAlchemy**, file storage on **Cloudflare R2**.

## Architecture Pattern

### Layered Architecture (Repository Pattern)

```
Routes (API endpoints)
   ↓
Services (business logic)
   ↓
Repositories (data access)
   ↓
Models (SQLAlchemy ORM)
```

**Key principle:** Routes should be thin - dependency injection of repositories into services, services orchestrate business logic, repositories handle database queries.

### Application Factory Pattern

- `app/main.py` exports app instance from `app/core/server.py:create_application()`
- All middleware, routes, configuration wired in factory
- Never create FastAPI instances elsewhere

### Routing Hierarchy

```
app/main.py (entry)
  └── app/core/server.py (factory)
      ├── / (index route)
      ├── /health (health_route.py)
      └── /api (router.py - v1 API prefix)
          ├── /auth (auth_route.py - login, profile, update)
          ├── /tenant (tenant_route.py - registration, approval)
          └── /proposal (proposal_route.py - AI classification)
```

**Adding routes:**

1. Create `app/api/routes/feature_route.py` with `router = APIRouter(prefix="/feature", tags=["Feature"])`
2. Include in `app/api/router.py`: `router_v1.include_router(feature_route.router)`
3. Routes auto-prefixed with `/api`

### Repository Pattern (NEW)

**All database access through repositories** in `app/repositories/`:

```python
# app/repositories/feature_repository.py
class FeatureRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: str) -> Optional[Feature]:
        return self.db.query(Feature).filter(Feature.id == id).first()

    def create(self, **kwargs) -> Feature:
        instance = Feature(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

# app/services/feature_service.py
class FeatureService:
    def __init__(self, feature_repo: FeatureRepository):
        self.feature_repo = feature_repo

    def business_logic(self, id: str) -> BaseResponse:
        feature = self.feature_repo.get_by_id(id)
        # ... business logic ...
        return create_success_response(data=feature.to_dict())

# app/api/routes/feature_route.py
def get_feature_service(db: Session = Depends(get_db)) -> FeatureService:
    return FeatureService(FeatureRepository(db))

@router.get("/{id}")
async def get_feature(id: str, service: FeatureService = Depends(get_feature_service)):
    return service.business_logic(id)
```

**Existing repositories:** `UserRepository`, `TenantRepository`, `BusinessDocumentRepository`

### Response Schema Pattern

**Always use standardized responses** from `app/core/schema.py`:

```python
from app.core.schema import BaseResponse, create_success_response, create_error_response

@router.get("/endpoint", response_model=BaseResponse)
async def endpoint():
    return create_success_response(message="Success", data={"key": "value"})
```

Response: `{"status": "success|failed|error|warning", "message": "...", "data": null | any}`

### Configuration Management

- All config in `app/core/config.py` using Pydantic Settings
- Environment variables loaded via `python-dotenv` from `.env` file
- Access config globally: `from app.core.config import settings`
- Use `settings.is_production` or `settings.is_development` for environment checks
- Config fields use `os.getenv()` - ensure `.env` has all vars from `.env.example`

### Dependency Injection Pattern

**Repository injection into services, services injected into routes:**

```python
# Route with multiple repository dependencies
def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    tenant_repo = TenantRepository(db)
    doc_repo = BusinessDocumentRepository(db)
    user_repo = UserRepository(db)
    return TenantService(tenant_repo, doc_repo, user_repo)

@router.post("/register")
async def register(
    data: TenantRegisterRequest,
    service: TenantService = Depends(get_tenant_service)
):
    return service.register_tenant(data)
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

### ML Components (IndoBERT Proposal Classification)

**Active ML feature:** Fine-tuned IndoBERT model for proposal classification (pass/reject)

- Model stored in `app/ml/indobert_full_proposal_finetuned/` (safetensors format)
- `ProposalClassifierService` in `app/services/proposal_classifier_service.py`
- Singleton pattern: `get_proposal_classifier()` dependency
- `PDFParserService` extracts structured sections from proposal PDFs
- Routes in `app/api/routes/proposal_route.py`:
  - `/api/proposal/classify/tenant/{tenant_id}` - classify from tenant's uploaded proposal
  - `/api/proposal/classify/url` - classify from PDF URL
  - `/api/proposal/classify/text` - classify from raw text
  - `/api/proposal/classify/sections` - classify from structured sections

**Pattern for ML services:**

```python
# Singleton instance
classifier_instance = None

def get_proposal_classifier() -> ProposalClassifierService:
    global classifier_instance
    if classifier_instance is None:
        classifier_instance = ProposalClassifierService()
    return classifier_instance
```

### Models Directory

`app/models/` is for **data models** (DTOs, ORM models), NOT ML models:

- **ORM models:** `user_model.py`, `tenant_model.py` (SQLAlchemy tables)
- **DTOs:** `app/models/dto/` - `auth_dto.py`, `tenant_dto.py`, `proposal_dto.py` (Pydantic)
- `app/models/__init__.py` centralizes imports for SQLAlchemy metadata
- Always import new models in `__init__.py` before running Alembic migrations

**Key models:**

- `User` - Short ID (4 chars), Firebase UID, role (admin/tenant/guest)
- `Tenant` - Incubator applicant with business info, status (pending/approved/rejected)
- `BusinessDocument` - Stores proposal URLs, logos, links to tenant

### Logging

- Import logger: `import logging; logger = logging.getLogger(__name__)`
- Log level controlled by `LOG_LEVEL` env var
- Request timing is automatically logged by middleware (see `server.py:add_timing`)

## File Upload & Cloud Storage

**Cloudflare R2** (S3-compatible) for file storage:

- `app/core/object_storage.py` - Singleton R2Client using boto3
- `app/services/file_upload_service.py` - Upload service with validation
- `file_upload_service` global instance for easy import
- Used by tenant registration for proposal PDFs, logos, documents

**Upload pattern:**

```python
from app.services.file_upload_service import file_upload_service

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        url = await file_upload_service.upload_file(
            file,
            folder="tenants",
            allowed_extensions=[".pdf", ".jpg"],
            max_size_mb=10
        )
        return create_success_response(data={"url": url})
    except Exception as e:
        return create_error_response(message=str(e))
```

**Config:** R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_PUBLIC_URL in `.env`

## Key Files Reference

| File/Directory                                | Purpose                                               |
| --------------------------------------------- | ----------------------------------------------------- |
| `app/core/server.py`                          | Application factory, middleware, root routes          |
| `app/core/config.py`                          | Settings (Pydantic), all env vars                     |
| `app/core/schema.py`                          | BaseResponse, create_success/error_response helpers   |
| `app/core/database.py`                        | SQLAlchemy engine, get_db dependency                  |
| `app/core/middleware.py`                      | Firebase auth middleware, get_current_user dependency |
| `app/core/object_storage.py`                  | R2Client singleton for Cloudflare R2                  |
| `app/core/utils.py`                           | generate_short_id() - 4-char IDs for users/tenants    |
| `app/api/router.py`                           | router_v1 aggregator for all API routes               |
| `app/api/routes/auth_route.py`                | Login, profile, update (Firebase auth)                |
| `app/api/routes/tenant_route.py`              | Register tenant, approve/reject (admin), list         |
| `app/api/routes/proposal_route.py`            | AI proposal classification endpoints                  |
| `app/services/tenant_service.py`              | Tenant registration, approval workflow                |
| `app/services/proposal_classifier_service.py` | IndoBERT model loading & inference                    |
| `app/services/pdf_parser_service.py`          | Extract sections from proposal PDFs                   |
| `app/services/file_upload_service.py`         | R2 file upload with validation                        |
| `app/repositories/tenant_repository.py`       | TenantRepository, BusinessDocumentRepository          |
| `app/repositories/user_repository.py`         | UserRepository for user queries                       |
| `app/models/user_model.py`                    | User ORM (short ID, Firebase UID, role enum)          |
| `app/models/tenant_model.py`                  | Tenant, BusinessDocument ORM (status enum)            |
| `app/ml/indobert_full_proposal_finetuned/`    | Fine-tuned IndoBERT model files                       |
| `docs/PROPOSAL_CLASSIFICATION.md`             | ML service architecture & usage guide                 |
| `docs/SETUP_AUTH.md`                          | Firebase setup instructions                           |

## Common Tasks

**Add API endpoint with repository pattern:**

1. Create ORM model in `app/models/` (if needed), import in `app/models/__init__.py`
2. Create repository in `app/repositories/feature_repository.py`
3. Create service in `app/services/feature_service.py` (inject repositories)
4. Create route in `app/api/routes/feature_route.py`:

   ```python
   def get_service(db: Session = Depends(get_db)) -> FeatureService:
       return FeatureService(FeatureRepository(db))

   @router.post("/", response_model=BaseResponse)
   async def create(data: FeatureDTO, service = Depends(get_service)):
       return service.create_feature(data)
   ```

5. Include in `app/api/router.py`: `router_v1.include_router(feature_route.router)`

**Add database model:**

1. Create in `app/models/feature_model.py` inheriting `Base`
2. Add `__tablename__`, `__table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}`
3. Add ID (CHAR(4) for short IDs or String/UUID), timestamps (created_at, updated_at)
4. Include `to_dict()` method
5. Import in `app/models/__init__.py`
6. Generate migration: `uv run alembic revision --autogenerate -m "Add feature table"`
7. Review migration, then `uv run alembic upgrade head`

**Add protected endpoint (requires auth):**

```python
from app.core.middleware import get_current_user_firebase_uid
from app.repositories.user_repository import UserRepository

@router.get("/protected")
async def protected(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db)
):
    user = UserRepository(db).get_by_firebase_uid(firebase_uid)
    return create_success_response(data={"user_id": user.id})
```

**Require admin role:**

```python
def require_admin_role(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db)
) -> str:
    user = UserRepository(db).get_by_firebase_uid(firebase_uid)
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    return user.id

@router.post("/admin-only")
async def admin_endpoint(user_id: str = Depends(require_admin_role)):
    # Only admins can access
    pass
```

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

**Backend protected route (use repositories, not raw queries):**

```python
from app.core.middleware import get_current_user_firebase_uid
from app.repositories.user_repository import UserRepository

@router.get("/protected")
async def protected(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db)
):
    user = UserRepository(db).get_by_firebase_uid(firebase_uid)
    return create_success_response(data=user.to_dict())
```

**Auth endpoints:**

- `POST /api/auth/login` - Login/register with Firebase token (creates user if not exists)
- `GET /api/auth/me` - Current user profile
- `PUT /api/auth/me` - Update profile
- `DELETE /api/auth/me` - Soft delete (set is_active=False)

**Tenant endpoints (with role checks):**

- `POST /api/tenant/register` - Submit tenant application (with file uploads)
- `GET /api/tenant` - List all tenants (admin only)
- `GET /api/tenant/{id}` - Get tenant details
- `GET /api/tenant/me` - Current user's tenant application
- `PUT /api/tenant/{id}/status` - Approve/reject tenant (admin only)

**Proposal classification endpoints:**

- `POST /api/proposal/classify/tenant/{tenant_id}` - Classify tenant's proposal
- `POST /api/proposal/classify/url` - Classify from PDF URL
- `POST /api/proposal/classify/text` - Classify raw text
- `POST /api/proposal/classify/sections` - Classify structured sections

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

**User & Tenant Roles:**

- `UserRole.ADMIN` - Approve/reject tenants, full system access
- `UserRole.TENANT` - Approved incubator participant (set when tenant approved)
- `UserRole.GUEST` - Default role, can register as tenant applicant

**Tenant Status Flow:**

1. Guest user submits `/api/tenant/register` → `TenantStatus.PENDING`
2. Admin reviews `/api/tenant/{id}/status` → `APPROVED` or `REJECTED`
3. If approved, user role upgraded to `UserRole.TENANT`

**Short ID System:**

Both User and Tenant use 4-char IDs (A-Z, 0-9): `generate_short_id()` from `app/core/utils`

```python
from app.core.utils import generate_short_id

id = generate_short_id()  # e.g., "A1B2"
# Check uniqueness in repository before committing
```

36^4 = 1,679,616 combinations - always check uniqueness in repository create methods
