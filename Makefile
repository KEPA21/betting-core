# ==============================
# Config
# ==============================
PY               := python3
VENV             := .venv
ACT              := . $(VENV)/bin/activate &&
UVICORN          := uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

ENV_FILE         := .env
-include $(ENV_FILE)
export

COMPOSE          := docker compose --env-file $(ENV_FILE) -f docker/docker-compose.yml

DB_HOST          ?= 127.0.0.1
DB_PORT          ?= 5433
DB_USER          ?= betting
DB_PASSWORD      ?= betting
DB_NAME          ?= betting_core
TEST_DB_NAME     ?= betting_core_test

DATABASE_URL     ?= postgresql+psycopg://$(DB_USER):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)/$(DB_NAME)
TEST_DATABASE_URL?= postgresql+psycopg://$(DB_USER):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)/$(TEST_DB_NAME)


# ==============================
# Help
# ==============================
.PHONY: help
help:
	@echo "Targets:"
	@echo "  venv                - skapa venv (.venv)"
	@echo "  install             - installera requirements (+ dev om fil finns)"
	@echo "  run                 - starta API (uvicorn --reload)"
	@echo "  test                - pytest med coverage"
	@echo "  lint                - ruff + black --check"
	@echo "  fmt                 - black app/"
	@echo "  openapi             - exportera OpenAPI till openapi.json"
	@echo "  compose-up          - starta compose (postgres/redis/api om definierat)"
	@echo "  compose-down        - stoppa compose"
	@echo "  compose-logs        - taila alla compose-loggar"
	@echo "  pg-logs             - taila postgres-loggar"
	@echo "  redis-cli           - öppna redis-cli via compose"
	@echo "  db-shell            - psql mot DB_HOST/DB_PORT/DB_NAME"
	@echo "  migrate             - alembic upgrade head (main)"
	@echo "  migrate-test        - alembic upgrade head (TEST_DATABASE_URL)"
	@echo "  seed-sql            - kör db/seed_test.sql mot TEST_DB_NAME"
	@echo "  seed-demo           - kör scripts/seed_demo_data.py"
	@echo "  pre-commit-install  - installera git hookar"
	@echo "  pre-commit-run      - kör pre-commit på hela repo"
	@echo "  loadtest-odds       - kör ditt loadtest_odds.py"
	@echo "  print-env           - skriv ut viktiga ENV"
	@echo "  clean               - städa pycache/coverage"
	@echo "  check               - lint + test"


# ==============================
# Env / venv / install
# ==============================
$(VENV):
	$(PY) -m venv $(VENV)

.PHONY: venv
venv: $(VENV)

.PHONY: install
install: venv
	$(ACT) pip install -U pip
	$(ACT) pip install -r requirements.txt
	@if [ -f requirements-dev.txt ]; then $(ACT) pip install -r requirements-dev.txt; fi


# ==============================
# Run / Test / Lint
# ==============================
.PHONY: run
run:
	$(ACT) $(UVICORN)

.PHONY: test
test:
	$(ACT) pytest -q --cov=app --cov-report=term-missing

.PHONY: lint
lint:
	$(ACT) ruff check app
	$(ACT) black --check app

.PHONY: fmt
fmt:
	$(ACT) black app

.PHONY: check
check: lint test


# ==============================
# OpenAPI
# ==============================
.PHONY: openapi
openapi:
	$(ACT) python scripts/export_openapi.py > openapi.json
	@echo "Wrote openapi.json"


# ==============================
# Docker compose helpers
# ==============================
.PHONY: compose-up
compose-up:
	$(COMPOSE) up -d

.PHONY: compose-down
compose-down:
	$(COMPOSE) down

.PHONY: compose-logs
compose-logs:
	$(COMPOSE) logs -f

.PHONY: pg-logs
pg-logs:
	$(COMPOSE) logs -f postgres || $(COMPOSE) logs -f db

.PHONY: redis-cli
redis-cli:
	$(COMPOSE) exec redis redis-cli


# ==============================
# DB / Alembic / Seeds
# ==============================
.PHONY: migrate
migrate:
	$(ACT) alembic -c db/alembic.ini upgrade head

.PHONY: migrate-test
migrate-test:
	DATABASE_URL="$(TEST_DATABASE_URL)" $(ACT) alembic -c db/alembic.ini upgrade head

.PHONY: db-shell
db-shell:
	@PGPASSWORD="$(DB_PASSWORD)" psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d $(DB_NAME)

.PHONY: seed-sql
seed-sql:
	@PGPASSWORD="$(DB_PASSWORD)" psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d $(TEST_DB_NAME) -v ON_ERROR_STOP=1 -f db/seed_test.sql

.PHONY: seed-demo
seed-demo:
	$(ACT) python scripts/seed_demo_data.py


# ==============================
# Pre-commit
# ==============================
.PHONY: pre-commit-install
pre-commit-install:
	$(ACT) pre-commit install

.PHONY: pre-commit-run
pre-commit-run:
	$(ACT) pre-commit run --all-files


# ==============================
# Loadtest
# ==============================
.PHONY: loadtest-odds
loadtest-odds:
	$(ACT) TOTAL=10000 BATCH=2000 CONC=8 python scripts/loadtest_odds.py


# ==============================
# Utils
# ==============================
.PHONY: print-env
print-env:
	@echo "ENV_FILE=$(ENV_FILE)"
	@echo "DATABASE_URL=$(DATABASE_URL)"
	@echo "TEST_DATABASE_URL=$(TEST_DATABASE_URL)"
	@echo "DB_HOST=$(DB_HOST) DB_PORT=$(DB_PORT) DB_USER=$(DB_USER) DB_NAME=$(DB_NAME)"

.PHONY: clean
clean:
	find . -name '__pycache__' -o -name '*.pyc' -delete
	rm -rf .pytest_cache .coverage
