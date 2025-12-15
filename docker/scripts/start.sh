#!/bin/bash
# Quick start script for Linux/Mac
# Run from project root: ./docker/scripts/start.sh

set -e

echo "================================"
echo "AI Inkubator - Docker Setup"
echo "================================"
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if firebase-credentials.json exists
if [ ! -f firebase-credentials.json ]; then
    echo "[WARNING] firebase-credentials.json not found!"
    echo "Please copy your Firebase credentials file to:"
    echo "  $(pwd)/firebase-credentials.json"
    echo
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "[INFO] Starting services with docker-compose..."
docker-compose up -d --build

echo
echo "================================"
echo "Services Started Successfully!"
echo "================================"
echo
echo "Backend API:  http://localhost:8000"
echo "API Docs:     http://localhost:8000/docs"
echo "Health:       http://localhost:8000/health"
echo "phpMyAdmin:   http://localhost:8081"
echo
echo "Useful commands:"
echo "  docker-compose logs -f backend  # View backend logs"
echo "  docker-compose ps               # Check status"
echo "  docker-compose down             # Stop all services"
echo
