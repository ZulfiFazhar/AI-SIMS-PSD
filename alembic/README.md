# Alembic Database Migrations

This directory contains database migration scripts managed by Alembic.

## 🆕 First Time Setup (Cloned Repository)

If you just cloned this repository, migration files already exist. Follow these steps:

### 1. Install Dependencies

```bash
uv sync
```

### 2. Create Database

Create your MySQL database:

```sql
CREATE DATABASE ai_inkubator;
```

### 3. Configure Environment Variables

Create/update your `.env` file:

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/ai_inkubator
```

### 4. Apply Existing Migrations

```bash
# This will run all migration files in alembic/versions/
uv run alembic upgrade head
```

### 5. Verify Setup

```bash
# Check current migration status
uv run alembic current

# View migration history
uv run alembic history
```

✅ **Done!** Your database is now synced with the latest schema.

---

## 📦 Initial Setup (New Project - No Migrations Yet)

If this is a brand new project without any migration files:

1. **Install Alembic** (already added to pyproject.toml):

   ```bash
   uv sync
   ```

2. **Environment Variables**:
   Ensure your `.env` file has the correct `DATABASE_URL`:

   ```env
   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/dbname
   ```

3. **Create Initial Migration**:

   ```bash
   uv run alembic revision --autogenerate -m "Initial migration - create users table"
   ```

4. **Apply Migration**:

   ```bash
   uv run alembic upgrade head
   ```

---

## Common Commands

### 1. Create Initial Migration (First Time Only)

Generate the initial migration for existing models:

```bash
# Auto-generate migration from current models
uv run alembic revision --autogenerate -m "Initial migration - create users table"
```

This will create a file in `alembic/versions/` with upgrade and downgrade scripts.

### 2. Apply Migrations

Run all pending migrations:

```bash
uv run alembic upgrade head
```

### 3. Create New Migration

After adding/modifying a model:

```bash
# Alembic will detect the changes automatically
uv run alembic revision --autogenerate -m "Add proposals table"

# Then apply the migration
uv run alembic upgrade head
```

### 4. Rollback Migration

Downgrade one version:

```bash
uv run alembic downgrade -1
```

Downgrade to specific revision:

```bash
uv run alembic downgrade <revision_id>
```

Rollback all migrations:

```bash
uv run alembic downgrade base
```

### 5. Check Migration Status

Show current revision:

```bash
uv run alembic current
```

Show migration history:

```bash
uv run alembic history --verbose
```

### 6. Manual Migration

Create empty migration file (for manual SQL):

```bash
uv run alembic revision -m "Custom migration"
```

## Migration Workflow Example

### Scenario: Adding a new "Proposal" model

1. **Create the model** in `app/models/proposal.py`:

   ```python
   from sqlalchemy import Column, Integer, String, Text
   from app.core.database import Base

   class Proposal(Base):
       __tablename__ = "proposals"
       id = Column(Integer, primary_key=True)
       title = Column(String(255), nullable=False)
       description = Column(Text)
   ```

2. **Import in models/**init**.py**:

   ```python
   from app.models.proposal import Proposal
   __all__ = ["User", "Proposal"]
   ```

3. **Generate migration**:

   ```bash
   uv run alembic revision --autogenerate -m "Add proposals table"
   ```

4. **Review the generated migration file** in `alembic/versions/`

5. **Apply migration**:

   ```bash
   uv run alembic upgrade head
   ```

6. **Commit migration file to git**

## Best Practices

### ✅ DO:

- **Always review** auto-generated migrations before applying
- **Test migrations** on development database first
- **Commit migration files** to version control
- **Use descriptive messages** for migrations
- **Add indexes and constraints** in migrations
- **Handle data migrations** separately if needed

### ❌ DON'T:

- Don't modify applied migrations (create new ones instead)
- Don't use `Base.metadata.create_all()` in production
- Don't skip reviewing auto-generated code
- Don't forget to add downgrade logic
- Don't apply migrations without backup in production

## Production Deployment

### First Time Deployment (New Server)

When deploying to a new production server for the first time:

```bash
# 1. Clone repository
git clone <repository-url>
cd <project-directory>

# 2. Install dependencies
uv sync

# 3. Create production database
mysql -u root -p
CREATE DATABASE ai_inkubator;
EXIT;

# 4. Configure environment
# Create .env with production DATABASE_URL
echo "DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/ai_inkubator" > .env

# 5. Apply all migrations (runs all files in alembic/versions/)
uv run alembic upgrade head

# 6. Verify
uv run alembic current

# 7. Start application
uv run fastapi run
```

### Regular Updates (Existing Server)

When updating an existing production server with new migrations:

1. **Before deployment**:

   ```bash
   # Check current migration status
   uv run alembic current

   # See what migrations will be applied
   uv run alembic history --verbose
   ```

2. **During deployment**:

   ```bash
   # Pull latest code (includes new migration files)
   git pull origin main

   # Install any new dependencies
   uv sync

   # **IMPORTANT: Backup database first!**
   mysqldump -u user -p ai_inkubator > backup_$(date +%Y%m%d_%H%M%S).sql

   # Apply new migrations
   uv run alembic upgrade head

   # Restart application
   systemctl restart fastapi-app
   ```

3. **Rollback if needed**:

   ```bash
   # Rollback last migration
   uv run alembic downgrade -1

   # Or restore from backup
   mysql -u user -p ai_inkubator < backup_20241217_143000.sql
   ```

### Zero-Downtime Deployment

For critical production systems:

```bash
# 1. Apply migrations first (before deploying new code)
uv run alembic upgrade head

# 2. Verify migrations succeeded
uv run alembic current

# 3. Deploy new application code
git pull && systemctl restart fastapi-app

# 4. Monitor logs
journalctl -u fastapi-app -f
```

## Troubleshooting

### Migration out of sync

If Alembic thinks migrations are out of sync:

```bash
# Stamp current database state
uv run alembic stamp head
```

### Reset migrations (development only)

```bash
# Drop all tables
uv run alembic downgrade base

# Reapply all migrations
uv run alembic upgrade head
```

### Merge conflicts in migrations

If multiple branches create migrations:

```bash
# Create a merge migration
uv run alembic merge heads -m "Merge migrations"
```

## Migration File Structure

```
alembic/
├── versions/           # Migration scripts
│   ├── 20241217_1430_abc123_initial_migration.py
│   └── 20241218_0900_def456_add_proposals_table.py
├── env.py             # Alembic environment configuration
├── script.py.mako     # Template for new migrations
└── README.md          # This file

alembic.ini            # Alembic configuration
```

## Disabling Auto-Creation in Production

To disable `Base.metadata.create_all()` in production, uncomment these lines in `app/core/database.py`:

```python
if settings.is_production:
    logger.info("Skipping auto table creation in production")
    return  # Force use of Alembic
```

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Auto-generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
