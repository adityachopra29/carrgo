#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install from https://docs.docker.com/get-docker/"
  exit 1
fi

if [ ! -f .env.production ]; then
  cp deploy/env.production.example .env.production
  echo ""
  echo "Created .env.production from template."
  echo "Edit it with your secrets (especially SECRET_KEY), then run:"
  echo "  ./deploy/deploy.sh"
  exit 1
fi

if grep -q '^SECRET_KEY=change-me' .env.production; then
  echo "Update SECRET_KEY in .env.production before deploying."
  echo "Generate one with: openssl rand -hex 32"
  exit 1
fi

# Update Caddy email if DEPLOY_EMAIL is set
if [ -n "${DEPLOY_EMAIL:-}" ]; then
  sed -i.bak "s/email you@adityachopra.tech/email ${DEPLOY_EMAIL}/" deploy/Caddyfile
  rm -f deploy/Caddyfile.bak
fi

echo "Building and starting Carrgo..."
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

echo ""
echo "Carrgo is running."
echo ""
echo "Next steps:"
echo "  1. Point DNS for carrgo.adityachopra.tech and api.carrgo.adityachopra.tech"
echo "     to this server's public IP (A records)."
echo "  2. Wait for DNS propagation (usually a few minutes)."
echo "  3. Caddy will automatically provision HTTPS certificates."
echo ""
echo "  Frontend: https://carrgo.adityachopra.tech"
echo "  API:      https://api.carrgo.adityachopra.tech"
echo "  Health:   https://api.carrgo.adityachopra.tech/health"
echo ""
echo "Logs:  docker compose -f docker-compose.prod.yml logs -f"
echo "Stop:  docker compose -f docker-compose.prod.yml down"
