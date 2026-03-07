SHELL := /bin/bash

UV ?= uv
COMPOSE ?= docker compose
COMPOSE_PROFILES ?= dev
NPM ?= npm
COMPOSE_PUBLIC_FILES ?= -f docker-compose.yml -f docker-compose.prod.yml

.PHONY: help install install-dev lint format-check test test-api-integration check i18n-tools-check i18n-compile i18n-check compose-config compose-config-public build up-dev up-prod up-public deploy-public down down-public logs logs-public ps health smoke-public db-rbac-verify frontend-install frontend-dev frontend-build frontend-preview frontend-check dev-full prod-ready

help:
	@printf "Available targets:\n"
	@printf "  install        Sync runtime dependencies\n"
	@printf "  install-dev    Sync runtime + dev dependencies\n"
	@printf "  lint           Run Ruff checks\n"
	@printf "  format-check   Run Ruff format check\n"
	@printf "  test           Run pytest\n"
	@printf "  test-api-integration Run API authz integration tests\n"
	@printf "  check          Run lint + format-check + test\n"
	@printf "  i18n-tools-check Ensure gettext tooling is installed\n"
	@printf "  i18n-compile   Compile gettext catalogs (.po -> .mo)\n"
	@printf "  i18n-check     Verify committed .mo files are up to date\n"
	@printf "  compose-config Validate docker compose config\n"
	@printf "  compose-config-public Validate public docker compose config\n"
	@printf "  build          Build docker images\n"
	@printf "  up-dev         Start stack with dev profile\n"
	@printf "  up-prod        Start stack with prod profile\n"
	@printf "  up-public      Start public VM stack (base + prod compose)\n"
	@printf "  deploy-public  Validate env, deploy public VM stack, run smoke checks\n"
	@printf "  down           Stop all local/public stacks\n"
	@printf "  down-public    Stop public VM stack\n"
	@printf "  logs           Follow docker compose logs\n"
	@printf "  logs-public    Follow public VM stack logs\n"
	@printf "  ps             Show docker compose services\n"
	@printf "  health         Check service /health endpoint\n"
	@printf "  smoke-public   Run public HTTPS smoke checks\n"
	@printf "  db-rbac-verify Verify DB role boundaries for engine/api\n"
	@printf "  frontend-install Install frontend dependencies\n"
	@printf "  frontend-dev   Start frontend Vite dev server\n"
	@printf "  frontend-build Build frontend production bundle\n"
	@printf "  frontend-preview Preview frontend production build\n"
	@printf "  frontend-check Run frontend build checks\n"
	@printf "  dev-full       Start full dev stack via docker compose\n"
	@printf "  prod-ready     Run production readiness checks\n"

install:
	$(UV) sync --all-extras

install-dev:
	$(UV) sync --dev --all-extras

lint: install-dev
	$(UV) run ruff check .

format-check: install-dev
	$(UV) run ruff format --check .

test: install-dev
	$(UV) run pytest -q -m "not integration"

test-api-integration: install-dev
	@test -n "$$API_TEST_DATABASE_URL" || { \
		echo "API_TEST_DATABASE_URL is required for integration tests."; \
		echo "Refusing to fall back to API_DATABASE_URL/DATABASE_URL."; \
		exit 1; \
	}
	$(UV) run pytest -m integration -q

check: lint format-check test

i18n-tools-check:
	@command -v msgfmt >/dev/null || { \
		echo "msgfmt not found. Install gettext first."; \
		echo "Debian/Ubuntu: sudo apt-get install gettext"; \
		echo "macOS (Homebrew): brew install gettext"; \
		exit 1; \
	}

i18n-compile: i18n-tools-check
	msgfmt -o locales/en/LC_MESSAGES/emails.mo locales/en/LC_MESSAGES/emails.po
	msgfmt -o locales/de/LC_MESSAGES/emails.mo locales/de/LC_MESSAGES/emails.po

i18n-check: i18n-tools-check
	msgfmt -o /tmp/emails.en.mo locales/en/LC_MESSAGES/emails.po
	msgfmt -o /tmp/emails.de.mo locales/de/LC_MESSAGES/emails.po
	cmp --silent /tmp/emails.en.mo locales/en/LC_MESSAGES/emails.mo
	cmp --silent /tmp/emails.de.mo locales/de/LC_MESSAGES/emails.mo

compose-config:
	$(COMPOSE) config > /dev/null

compose-config-public:
	COMPOSE_PROFILES=prod $(COMPOSE) $(COMPOSE_PUBLIC_FILES) config > /dev/null

build:
	$(COMPOSE) build

up-dev:
	COMPOSE_PROFILES=dev $(COMPOSE) up -d --build

up-prod:
	COMPOSE_PROFILES=prod $(COMPOSE) up -d --build

up-public:
	COMPOSE_PROFILES=prod $(COMPOSE) $(COMPOSE_PUBLIC_FILES) up -d --build

deploy-public:
	./scripts/deploy_public_stack.sh

down:
	$(COMPOSE) down --remove-orphans
	COMPOSE_PROFILES=prod $(COMPOSE) $(COMPOSE_PUBLIC_FILES) down --remove-orphans

down-public:
	COMPOSE_PROFILES=prod $(COMPOSE) $(COMPOSE_PUBLIC_FILES) down

logs:
	$(COMPOSE) logs -f

logs-public:
	COMPOSE_PROFILES=prod $(COMPOSE) $(COMPOSE_PUBLIC_FILES) logs -f

ps:
	$(COMPOSE) ps

health:
	curl -fsS "http://localhost:8090/health"

smoke-public:
	@test -n "$$PUBLIC_API_DOMAIN" || { echo "PUBLIC_API_DOMAIN is required"; exit 1; }
	@test -n "$$PUBLIC_APP_DOMAIN" || { echo "PUBLIC_APP_DOMAIN is required"; exit 1; }
	@test -n "$$PUBLIC_APP_WWW_DOMAIN" || { echo "PUBLIC_APP_WWW_DOMAIN is required"; exit 1; }
	curl -fsS "https://$$PUBLIC_API_DOMAIN/health/live"
	curl -fsS "https://$$PUBLIC_API_DOMAIN/health/ready"
	curl -fsS "https://$$PUBLIC_APP_DOMAIN" > /dev/null

db-rbac-verify:
	$(UV) run python scripts/verify_db_rbac.py

frontend-install:
	$(NPM) --prefix frontend install

frontend-dev:
	$(NPM) --prefix frontend run dev

frontend-build:
	$(NPM) --prefix frontend run build

frontend-preview:
	$(NPM) --prefix frontend run preview

frontend-check: frontend-build

dev-full: up-dev
	@printf "Dev stack is running. Open http://localhost:5173\n"

prod-ready: check i18n-check compose-config
