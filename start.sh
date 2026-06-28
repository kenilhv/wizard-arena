#!/usr/bin/env bash
# One-shot build + run for Replit (single-service: FastAPI serves API + built UI).
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "[arena] python deps..."
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt

# Build the frontend once (delete frontend/dist to force a rebuild).
if [ ! -d frontend/dist ]; then
  echo "[arena] building frontend (first run, ~1-2 min)..."
  cd frontend
  npm install
  npm run build
  cd "$ROOT"
fi

echo "[arena] serving on 0.0.0.0:${PORT:-8000}"
cd backend
exec python -m uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}"
