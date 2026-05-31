#!/bin/bash
# ── NeoEvent Backend — Local Dev Startup ──────────────────────────────────────
# Uses Docker Compose (docker-compose.dev.yml) to start all backend services:
#   - PostgreSQL (with pgvector)
#   - Redis
#   - Django (runserver, hot-reload)
#   - Celery worker
#   - FastAPI classifier microservice

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║        NeoEvent Backend — Dev Startup        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌  Docker is not running. Please start Docker Desktop first."
  exit 1
fi

echo "🐳  Starting all services via Docker Compose..."
echo ""

docker compose -f docker-compose.dev.yml up --build "$@"
