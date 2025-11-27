# FastAPI UV Backend

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
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

- [Python](https://www.python.org/downloads/) (version 3.10 or higher)
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

## Project Structure

```
fastapi-uv/
├── app/
│   ├── api/                  # API module with routes
│   │   └── routes.py
│   ├── core/                 # Core configuration and application logic
│   │   └── config.py
│   ├── ml/                   # Machine learning related code
│   │   ├── inference/        # Inference logic
│   │   ├── models/           # ML model files (.pt, .h5, .pkl)
│   │   └── preprocessing/    # Training scripts
│   ├── models/               # Python models (ORM, DTOs, Domain)
│   ├── services/             # Business logic and service layer
│   └── main.py               # FastAPI application entry point
├── .env                      # Configuration file (ignored by git)
├── Dockerfile                # Docker build definition
├── pyproject.toml            # Project and dependency definition
└── uv.lock                   # Lock file for dependencies
```

## API Endpoints

Here are the available endpoints:

- **Documentation**

  - **GET** `/docs`
  - **Description:** Documentation endpoint.

## Docker

This project can be built and run using Docker.

1. **Build the Docker Image:**
   The `docker-build.sh` script is provided for convenience.

   ```sh
   ./docker-build.sh
   ```

   Alternatively, build it manually:

   ```sh
   docker build -t fastapi-uv-backend .
   ```

2. **Run the Container:**

   ```sh
   docker run -p 8000:8000 --env-file .env fastapi-uv-backend
   ```

   The application will be accessible at `http://localhost:8000`.
