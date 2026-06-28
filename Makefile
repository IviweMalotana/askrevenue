.DEFAULT_GOAL := help
SHELL := /bin/bash

# Run uv from the api/ directory for all Python commands.
UV := cd api && uv

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- Infrastructure --------------------------------------------------------

.PHONY: db-up
db-up: ## Start the local Postgres container
	docker compose up -d db
	@echo "Waiting for Postgres to become healthy..."
	@until docker compose exec -T db pg_isready -U askrevenue -d askrevenue >/dev/null 2>&1; do sleep 1; done
	@echo "Postgres is ready."

.PHONY: db-down
db-down: ## Stop Postgres (keeps data volume)
	docker compose down

.PHONY: db-reset
db-reset: ## Stop Postgres and DELETE all data
	docker compose down -v

# --- Backend ---------------------------------------------------------------

.PHONY: install
install: ## Install Python deps via uv
	$(UV) sync

.PHONY: migrate
migrate: ## Apply Alembic migrations
	$(UV) run alembic upgrade head

.PHONY: grant-ro
grant-ro: ## Re-apply SELECT grants to the read-only role
	docker compose exec -T db psql -U askrevenue -d askrevenue \
		-c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO askrevenue_ro;"

.PHONY: seed
seed: db-up migrate grant-ro ## Migrate + seed a rich demo dataset (one command, zero setup)
	$(UV) run python -m app.seed

.PHONY: api
api: ## Run the FastAPI dev server on :8000
	$(UV) run uvicorn app.main:app --reload --port 8000

# --- Frontend --------------------------------------------------------------

.PHONY: web-install
web-install: ## Install web deps
	cd web && npm install

.PHONY: web
web: ## Run the Next.js dev server on :3000
	cd web && npm run dev

# --- Convenience -----------------------------------------------------------

.PHONY: dev
dev: ## Reminder of the two processes to run for local dev
	@echo "Run these in two terminals:"
	@echo "  make api   # backend  -> http://localhost:8000"
	@echo "  make web   # frontend -> http://localhost:3000"
