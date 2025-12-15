.PHONY: help build up down logs restart clean test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build all services
	docker-compose build

up: ## Start all services
	docker-compose up -d

up-build: ## Build and start all services
	docker-compose up -d --build

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-db: ## View database logs only
	docker-compose logs -f db

restart: ## Restart all services
	docker-compose restart

restart-backend: ## Restart backend only
	docker-compose restart backend

ps: ## Show running containers
	docker-compose ps

shell-backend: ## Access backend container shell
	docker-compose exec backend sh

shell-db: ## Access database shell
	docker-compose exec db mysql -u inkubator -pinkubator inkubator_db

clean: ## Stop and remove all containers, volumes
	docker-compose down -v

test: ## Test backend health
	@echo "Testing backend health..."
	@curl -f http://localhost:8000/health || echo "Backend not responding"

backup-db: ## Backup database
	docker-compose exec db mysqldump -u inkubator -pinkubator inkubator_db > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up to backup_$$(date +%Y%m%d_%H%M%S).sql"

dev: ## Start services for development
	@echo "Starting development environment..."
	docker-compose up -d db phpmyadmin
	@echo "Database and phpMyAdmin started. Run backend locally with: uv run fastapi dev"

prod: up-build ## Deploy production environment

status: ## Show service status and URLs
	@echo "Service Status:"
	@docker-compose ps
	@echo "\nAccess URLs:"
	@echo "  Backend API:  http://localhost:8000"
	@echo "  API Docs:     http://localhost:8000/docs"
	@echo "  phpMyAdmin:   http://localhost:8081"
