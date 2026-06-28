#!/usr/bin/env bash
# One-shot build + run for Replit (single-service: FastAPI serves API + built UI).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PORT="${PORT:-8000}"
export PORT
export AUTO_SEED="${AUTO_SEED:-0}"

echo "[arena] root=$ROOT port=$PORT auto_seed=$AUTO_SEED"

echo "[arena] python deps..."
if [ ! -d .venv ]; then python3 -m venv .venv; fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt

# Rebuild frontend when missing or when VITE secrets were added after first build.
BUILD_STAMP="frontend/dist/.replit-build-stamp"
NEED_BUILD=0
if [ ! -d frontend/dist ] || [ ! -f frontend/dist/index.html ]; then
  NEED_BUILD=1
fi
if [ -n "${VITE_INSFORGE_URL:-}" ] && [ ! -f "$BUILD_STAMP" ]; then
  NEED_BUILD=1
fi

if [ "$NEED_BUILD" = "1" ]; then
  echo "[arena] building frontend (~1-2 min)..."
  cd frontend
  npm install
  npm run build
  date -u +%Y-%m-%dT%H:%M:%SZ > "../$BUILD_STAMP"
  cd "$ROOT"
else
  echo "[arena] using existing frontend/dist (delete it to force rebuild)"
fi

echo "[arena] starting uvicorn on 0.0.0.0:$PORT"
cd backend
exec python -m uvicorn app:app --host 0.0.0.0 --port "$PORT"
