.PHONY: up down restart logs build shell db-shell clean migrate import help

help:
	@echo "Available commands:"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - Show logs (Ctrl+C to exit)"
	@echo "  make build       - Rebuild containers"
	@echo "  make shell       - Connect to web container shell"
	@echo "  make db-shell    - Connect to PostgreSQL"
	@echo "  make migrate     - Apply database migrations"
	@echo "  make import      - Import data from CSV"
	@echo "  make clean       - Stop and remove containers, volumes"
	@echo "  make tailwind    - Build Tailwind CSS"

up:
	docker-compose up -d
	@echo.
	@echo Services started!
	@echo Site: http://localhost:8765
	@echo PostgreSQL: localhost:5433
	@echo Redis: localhost:6379
	@echo.
	@echo View logs: make logs

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

build:
	docker-compose build
	@echo Containers rebuilt!

shell:
	docker-compose exec web bash

db-shell:
	docker-compose exec db psql -U bigear_user -d bigear_db

migrate:
	docker-compose exec web alembic upgrade head
	@echo Migrations applied!

import:
	docker-compose exec web python scripts/import_audiobooks.py
	@echo Import completed!

clean:
	docker-compose down -v
	@echo All containers and volumes removed!

tailwind:
	npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch
