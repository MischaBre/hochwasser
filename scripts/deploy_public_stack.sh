#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
REPO_ROOT="$(realpath "${SCRIPT_DIR}/..")"

if [[ ! -f "${REPO_ROOT}/.env" ]]; then
  echo "Missing ${REPO_ROOT}/.env"
  echo "Copy .env.prod.example to .env and fill required values first."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "${REPO_ROOT}/.env"
set +a

required_vars=(
  PUBLIC_APP_DOMAIN
  PUBLIC_APP_WWW_DOMAIN
  PUBLIC_API_DOMAIN
  VITE_API_BASE_URL
  VITE_SUPABASE_URL
  VITE_SUPABASE_PUBLISHABLE_KEY
  VITE_SITE_URL
  DATABASE_URL
  API_DATABASE_URL
  FLYWAY_URL
  FLYWAY_USER
  FLYWAY_PASSWORD
  SUPABASE_JWKS_URL
  SUPABASE_ISSUER
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  API_CORS_ALLOW_ORIGINS
  SMTP_HOST
  SMTP_PORT
  SMTP_SENDER
  TZ
)

for key in "${required_vars[@]}"; do
  value="${!key:-}"
  if [[ -z "${value}" ]]; then
    echo "Missing required env var: ${key}"
    exit 1
  fi
done

if [[ "${VITE_API_BASE_URL}" != "https://${PUBLIC_API_DOMAIN}" ]]; then
  echo "VITE_API_BASE_URL must match https://${PUBLIC_API_DOMAIN}"
  exit 1
fi

if [[ "${VITE_SITE_URL}" != "https://${PUBLIC_APP_DOMAIN}" ]]; then
  echo "VITE_SITE_URL must match https://${PUBLIC_APP_DOMAIN}"
  exit 1
fi

if [[ "${API_CORS_ALLOW_ORIGINS}" != *"https://${PUBLIC_APP_DOMAIN}"* ]]; then
  echo "API_CORS_ALLOW_ORIGINS must include https://${PUBLIC_APP_DOMAIN}"
  exit 1
fi

if [[ "${PUBLIC_APP_WWW_DOMAIN}" != "www.${PUBLIC_APP_DOMAIN}" ]]; then
  echo "PUBLIC_APP_WWW_DOMAIN should be www.${PUBLIC_APP_DOMAIN}"
  exit 1
fi

echo "Deploying public stack for ${PUBLIC_APP_DOMAIN} (+ ${PUBLIC_APP_WWW_DOMAIN}) and ${PUBLIC_API_DOMAIN}"

docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "Running smoke checks"
curl -fsS "https://${PUBLIC_API_DOMAIN}/health/live" > /dev/null
curl -fsS "https://${PUBLIC_API_DOMAIN}/health/ready" > /dev/null
curl -fsS "https://${PUBLIC_APP_DOMAIN}" > /dev/null

echo "Deployment succeeded"
