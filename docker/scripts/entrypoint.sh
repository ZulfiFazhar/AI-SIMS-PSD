#!/bin/sh
# Entrypoint script for backend container
# Waits for database to be ready before starting the application

set -e

echo "Waiting for database to be ready..."

# Wait for database
until nc -z -v -w30 db 3306
do
  echo "Waiting for database connection..."
  sleep 2
done

echo "Database is ready!"
echo "Starting FastAPI application..."

# Execute CMD from Dockerfile
exec "$@"
