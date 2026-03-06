SHELL := /bin/bash

UV ?= uv
COMPOSE ?= docker compose
COMPOSE_PROFILES ?= dev
NPM ?= npm

.PHONY: help install install-dev lint format-check test test-api-integration check i18n-tools-check i18n-compile i18n-check compose-config build up-dev up-prod down logs ps health db-rbac-verify frontend-install frontend-dev frontend-build frontend-preview frontend-check dev-full prod-ready

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
	@printf "  build          Build docker images\n"
	@printf "  up-dev         Start stack with dev profile\n"
	@printf "  up-prod        Start stack with prod profile\n"
	@printf "  down           Stop stack\n"
	@printf "  logs           Follow docker compose logs\n"
	@printf "  ps             Show docker compose services\n"
	@printf "  health         Check service /health endpoint\n"
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

lint:
	$(UV) run ruff check .

format-check:
	$(UV) run ruff format --check .

test:
	$(UV) run pytest -q -m "not integration"

test-api-integration:
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

build:
	$(COMPOSE) build

up-dev:
	COMPOSE_PROFILES=dev $(COMPOSE) up -d --build

up-prod:
	COMPOSE_PROFILES=prod $(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

health:
	curl -fsS "http://localhost:8090/health"

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
