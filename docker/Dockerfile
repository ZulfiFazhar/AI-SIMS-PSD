# Base image
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv and curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* \
 && curl -LsSf https://astral.sh/uv/install.sh | sh \
 && ln -s /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files for layer caching
COPY pyproject.toml ./
COPY uv.lock ./

# Create venv and install dependencies (production only)
RUN uv sync --frozen --no-dev

# Copy application code
COPY app ./app

# Re-sync to ensure editable paths are included
RUN uv sync --frozen --no-dev

# Expose port
EXPOSE 8000

# Run FastAPI application
CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
