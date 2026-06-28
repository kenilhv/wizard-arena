#!/usr/bin/env bash
# Render build: Python deps + Vite frontend (env vars must be set in Render dashboard).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[render] Python $(python --version 2>&1)"
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "[render] Node $(node --version 2>&1)"
cd frontend
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi
npm run build

echo "[render] frontend/dist ready"
