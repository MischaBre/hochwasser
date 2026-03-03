SHELL := /bin/bash

UV ?= uv
COMPOSE ?= docker compose
COMPOSE_PROFILES ?= dev

.PHONY: help install install-dev lint format-check test check i18n-tools-check i18n-compile i18n-check compose-config build up-dev up-prod down logs ps health prod-ready

help:
	@printf "Available targets:\n"
	@printf "  install        Sync runtime dependencies\n"
	@printf "  install-dev    Sync runtime + dev dependencies\n"
	@printf "  lint           Run Ruff checks\n"
	@printf "  format-check   Run Ruff format check\n"
	@printf "  test           Run pytest\n"
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
	@printf "  prod-ready     Run production readiness checks\n"

install:
	$(UV) sync

install-dev:
	$(UV) sync --dev

lint:
	$(UV) run ruff check .

format-check:
	$(UV) run ruff format --check .

test:
	$(UV) run pytest -q

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

prod-ready: check i18n-check compose-config
