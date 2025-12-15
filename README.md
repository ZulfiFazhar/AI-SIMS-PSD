# FastAPI UV Backend

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.117.1-green.svg)](https://fastapi.tiangolo.com/)
[![uv](https://img.shields.io/badge/uv-powered-green.svg)](https://github.com/astral-sh/uv)

A backend service built with FastAPI and managed using `uv` for AI-related operations.

## Description

This project provides a robust foundation for building AI services, featuring best practices in project structure, configuration management, and deployment. It leverages `uv` for extremely fast dependency and virtual environment management.

## Features

- **Modern Framework:** Built on [FastAPI](https://fastapi.tiangolo.com/) for high performance and rapid API development.
- **Fast Dependency Management:** Uses [`uv`](https://github.com/astral-sh/uv) for instantaneous package installation and dependency resolution.
- **Centralized Configuration:** Easy configuration management through environment variables with Pydantic.
- **Docker Ready:** Includes a `Dockerfile` for building and deploying the application as a container.
- **Clear Project Structure:** Logically organized for scalability and maintenance.

## Getting Started

Follow these steps to set up the local development environment.

### Prerequisites

- [Python](https://www.python.org/downloads/) (version 3.12 or higher)
- [`uv`](https://github.com/astral-sh/uv):

  ```sh
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

### Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/ZulfiFazhar/FastAPI-UV-Template.git
   cd FastAPI-UV-Template
   ```

2. **Create and activate the virtual environment:**

   ```sh
   # Create a virtual environment in .venv
   uv venv

   # Activate (macOS/Linux)
   source .venv/bin/activate

   # Activate (Windows)
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   `uv` will sync the dependencies from `pyproject.toml` and `uv.lock`.

   ```sh
   uv sync
   ```

   To install development dependencies (like `ruff` and `pytest`), use:

   ```sh
   uv sync --dev
   ```

### Configuration

The application uses a `.env` file to manage configuration. Copy `.env.example` or create a new `.env` file in the project root.

## Running the Application

Use `uv run` to execute the application server.

- **Development Mode (with auto-reload):**

  ```sh
  uv run fastapi dev
  ```

- **Production Mode:**

  ```sh
  uv run fastapi run
  ```

The application will be available at `http://localhost:8000`.

## Code Quality

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

### Linting

Check code for issues:

```sh
# Check all files
uv run ruff check .

# Check specific directory
uv run ruff check app/

# Auto-fix fixable issues
uv run ruff check . --fix
```

### Formatting

Format code with Ruff:

```sh
# Check formatting (without changing files)
uv run ruff format . --check

# Format all files
uv run ruff format .

# Format specific directory
uv run ruff format app/
```

### Combined Workflow

```sh
# 1. Fix linting issues
uv run ruff check . --fix

# 2. Format code
uv run ruff format .
```

### Pre-commit Hook (Optional)

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
uv run ruff check . --fix
uv run ruff format .
```

## Project Structure

```
ai-inkubator/
├── app/
│   ├── api/                      # API module with routes
│   │   ├── v1/                   # API version 1
│   │   │   ├── router.py         # V1 route aggregator
│   │   │   └── routes/           # V1 endpoints
│   │   │       ├── auth_route.py # Authentication endpoints
│   │   │       └── ping_route.py # Ping endpoint
│   │   └── health_route.py       # Health check endpoint
│   ├── core/                     # Core configuration and application logic
│   │   ├── config.py             # Settings management
│   │   ├── database.py           # Database connection
│   │   ├── schema.py             # Standard response schemas
│   │   ├── security.py           # Firebase authentication
│   │   └── server.py             # Application factory
│   ├── ml/                       # Machine learning related code
│   │   ├── inference/            # Inference logic
│   │   ├── models/               # ML model files (.pt, .h5, .pkl)
│   │   └── preprocessing/        # Preprocessing scripts
│   ├── models/                   # Python models (ORM, DTOs)
│   │   ├── auth_dto.py           # Authentication DTOs
│   │   └── user.py               # User SQLAlchemy model
│   ├── services/                 # Business logic and service layer
│   │   ├── auth_service.py       # Authentication service
│   │   └── health.py             # Health check service
│   └── main.py                   # FastAPI application entry point
├── docker/                       # Docker-related files
│   ├── Dockerfile                # Multi-stage backend build
│   ├── .dockerignore             # Build context exclusions
│   ├── README.md                 # Docker documentation
│   └── scripts/                  # Docker helper scripts
│       ├── start.bat/sh          # Quick start
│       ├── stop.bat/sh           # Quick stop
│       ├── entrypoint.sh         # Container entrypoint
│       └── wait-for-db.sh        # Database readiness
├── .env                          # Configuration file (ignored by git)
├── .env.example                  # Example configuration
├── docker-compose.yaml           # Multi-service orchestration
├── docker-start.bat/sh           # Root wrapper scripts
├── docker-stop.bat/sh            # Root wrapper scripts
├── pyproject.toml                # Project and dependency definition
└── uv.lock                       # Lock file for dependencies
```

## API Endpoints

Here are the available endpoints:

- **Documentation**

  - **GET** `/docs` - Swagger UI documentation
  - **GET** `/health` - Health check endpoint

- **Authentication** (Firebase Auth + MySQL)
  - **POST** `/api/v1/auth/login` - Login/register with Firebase token
  - **GET** `/api/v1/auth/me` - Get current user profile (protected)
  - **PUT** `/api/v1/auth/me` - Update user profile (protected)
  - **DELETE** `/api/v1/auth/me` - Deactivate account (protected)

For detailed API testing guide, see [TESTING_GUIDE.md](TESTING_GUIDE.md)

## Docker Deployment

### Quick Start with Docker Compose

**Recommended**: Use Docker Compose to run the complete stack (Backend + MySQL + phpMyAdmin):

```sh
# 1. Prepare Firebase credentials
cp /path/to/your/firebase-credentials.json ./firebase-credentials.json

# 2. Start all services (Windows)
docker-start.bat

# Or (Linux/Mac)
./docker-start.sh

# Or manually
docker-compose up -d --build

# 3. View logs
docker-compose logs -f backend

# 4. Access services:
#    - Backend API: http://localhost:8000
#    - API Docs: http://localhost:8000/docs
#    - phpMyAdmin: http://localhost:8081
```

**Using Makefile** (easier):

```sh
make help           # Show all available commands
make up-build       # Build and start all services
make logs-backend   # View backend logs
make status         # Show service status
```

**Docker Files Organization:**

```
docker/
├── Dockerfile              # Multi-stage build
├── .dockerignore           # Build exclusions
├── README.md               # Docker documentation
└── scripts/
    ├── start.bat/sh        # Quick start scripts
    ├── stop.bat/sh         # Quick stop scripts
    ├── entrypoint.sh       # Container entrypoint
    └── wait-for-db.sh      # Database readiness check
```

For detailed Docker guide, see [DOCKER_GUIDE.md](DOCKER_GUIDE.md)

### Manual Docker Build (Single Container)

If you only want to build the backend container:

```sh
# Build the image from docker/ folder
docker build -f docker/Dockerfile -t fastapi-uv-backend .

# Run with environment variables
docker run -p 8000:8000 --env-file .env fastapi-uv-backend
```

**Note**: Manual build requires external MySQL and proper `.env` configuration.
