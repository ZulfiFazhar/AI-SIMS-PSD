# Docker Scripts and Configuration

This directory contains all Docker-related files for the project.

## Files

- **Dockerfile** - Production Docker image definition
- **.dockerignore** - Files to exclude from Docker build context
- **scripts/** - Helper scripts for Docker operations

## Usage

All Docker commands should be run from the project root:

```bash
# Build image
docker build -f docker/Dockerfile -t ai-inkubator-backend .

# Or use docker-compose (recommended)
docker-compose up -d --build
```

## Structure

```
docker/
├── Dockerfile           # Main production Dockerfile
├── .dockerignore       # Build context exclusions
└── scripts/
    ├── entrypoint.sh   # Container entrypoint (if needed)
    ├── wait-for-db.sh  # Database wait script (optional)
    └── ...
```

## Notes

- docker-compose.yaml stays in project root for easier access
- All Dockerfile paths are relative to project root (context)
- Use .dockerignore to optimize build time and image size
