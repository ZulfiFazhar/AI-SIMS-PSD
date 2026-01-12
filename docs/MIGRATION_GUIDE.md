# Database Migration Quick Start

## 🆕 **First Time Clone Project? Start Here!**

If you just cloned this project, the migration files already exist in the repo. You only need to **apply** them, not create new ones.

### Step 1: Install Dependencies

```bash
uv sync
```

### Step 2: Setup Database

Create your MySQL database:

```sql
CREATE DATABASE inkubator;
```

### Step 3: Configure Environment

Set your `DATABASE_URL` in `.env`:

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/inkubator
```

### Step 4: Apply Existing Migrations

```bash
# Apply all migrations from alembic/versions/
uv run alembic upgrade head
```

### Step 5: Verify

```bash
# Check current migration status
uv run alembic current

# Should show the latest migration revision
```

✅ **Done!** Your database is now set up with all tables.

---

## 🔨 **Starting Fresh Project? (No Migration Files Yet)**

If you're setting up Alembic for the first time on a new project:

### 1. Install Dependencies

```bash
uv sync
```

### 2. Create Initial Migration

Generate migration from your current User model:

```bash
uv run alembic revision --autogenerate -m "Initial migration - create users table"
```

This creates a migration file in `alembic/versions/`

### 3. Review the Migration

Open the generated file in `alembic/versions/` and verify the SQL operations look correct.

### 4. Apply Migration

```bash
uv run alembic upgrade head
```

✅ Your database now has the `users` table!

## 📝 Daily Workflow

### Adding/Modifying a Model

1. **Make changes** to your model (e.g., `app/models/user.py`)

2. **Generate migration**:

   ```bash
   uv run alembic revision --autogenerate -m "Add phone_number column to users"
   ```

3. **Review** the generated migration file

4. **Apply**:

   ```bash
   uv run alembic upgrade head
   ```

5. **Commit** the migration file to git

### Rollback a Migration

```bash
# Rollback last migration
uv run alembic downgrade -1

# Rollback to specific version
uv run alembic downgrade <revision_id>

# Rollback everything
uv run alembic downgrade base
```

## 🔍 Useful Commands

```bash
# Check current migration status
uv run alembic current

# Show migration history
uv run alembic history --verbose

# Show SQL that would be executed (without running)
uv run alembic upgrade head --sql
```

## 📋 Example: Adding a Proposals Table

1. Create `app/models/proposal.py`:

   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
   from datetime import datetime, timezone
   from app.core.database import Base

   class Proposal(Base):
       __tablename__ = "proposals"

       id = Column(Integer, primary_key=True, autoincrement=True)
       tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
       title = Column(String(255), nullable=False)
       description = Column(Text)
       status = Column(String(50), default="pending")
       created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
   ```

2. Add to `app/models/__init__.py`:

   ```python
   from app.models.proposal import Proposal
   __all__ = ["User", "Proposal"]
   ```

3. Generate and apply:
   ```bash
   uv run alembic revision --autogenerate -m "Add proposals table"
   uv run alembic upgrade head
   ```

## 🛡️ Production Deployment

```bash
# 1. Pull latest code with migration files
git pull origin main

# 2. Install dependencies
uv sync

# 3. Apply migrations
uv run alembic upgrade head

# 4. Start application
uv run fastapi run
```

## ⚠️ Important Notes

- ✅ **Always review** auto-generated migrations
- ✅ **Test on development** database first
- ✅ **Backup production** database before applying migrations
- ✅ **Commit migration files** to version control
- ❌ **Never modify** already-applied migrations
- ❌ **Don't use** `Base.metadata.create_all()` in production

## 📚 Full Documentation

See [alembic/README.md](alembic/README.md) for comprehensive guide.
