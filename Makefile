# ==== Config ====
PY := python3
VENV := .venv
ACT := . $(VENV)/bin/activate &&
UVICORN := uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
COMPOSE := docker compose -f docker/docker-compose.yml

# ==== Help ====
.PHONY: help
help:
	@echo "Targets:"
	@echo "  venv            - skapa venv (.venv)"
	@echo "  install         - installera requirements (+ dev om fil finns)"
	@echo "  run             - starta API (uvicorn --reload)"
	@echo "  test            - pytest med coverage"
	@echo "  lint            - ruff + black --check"
	@echo "  fmt             - black app/"
	@echo "  openapi         - exportera OpenAPI till openapi.json"
	@echo "  compose-up      - starta docker (postgres/redis/api om definierat)"
	@echo "  compose-down    - stoppa docker"
	@echo "  pg-logs         - taila postgres-loggar (service: postgres|db)"
	@echo "  redis-cli       - öppna redis-cli via compose"
	@echo "  migrate         - alembic upgrade head (om du använder Alembic)"
	@echo "  seed            - kör ev. seed-script"
	@echo "  loadtest-odds   - kör ditt loadtest_odds.py"
	@echo "  clean           - städa pycache/coverage"

# ==== Env / venv ====
$(VENV):
	$(PY) -m venv $(VENV)

.PHONY: venv
venv: $(VENV)

.PHONY: install
install: venv
	$(ACT) pip install -U pip
	$(ACT) pip install -r requirements.txt
	@if [ -f requirements-dev.txt ]; then $(ACT) pip install -r requirements-dev.txt; fi

# ==== Run / Test / Lint ====
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

# ==== OpenAPI ====
.PHONY: openapi
openapi:
	$(ACT) python scripts/export_openapi.py > openapi.json

# ==== Docker compose helpers ====
.PHONY: compose-up
compose-up:
	$(COMPOSE) up -d

.PHONY: compose-down
compose-down:
	$(COMPOSE) down

.PHONY: pg-logs
pg-logs:
	# justera service-namnet om din compose använder 'db' i stället för 'postgres'
	$(COMPOSE) logs -f postgres || $(COMPOSE) logs -f db

.PHONY: redis-cli
redis-cli:
	# kör redis-cli via compose (funkar oavsett faktiskt container-namn)
	$(COMPOSE) exec redis redis-cli

# ==== DB / Seeds / Loadtest ====
.PHONY: migrate
migrate:
	$(ACT) alembic upgrade head

.PHONY: seed
seed:
	$(ACT) python scripts/seed_demo_data.py

.PHONY: loadtest-odds
loadtest-odds:
	$(ACT) TOTAL=10000 BATCH=2000 CONC=8 python3 scripts/loadtest_odds.py

# ==== Clean ====
.PHONY: clean
clean:
	find . -name '__pycache__' -o -name '*.pyc' -delete
	rm -rf .pytest_cache .coverage