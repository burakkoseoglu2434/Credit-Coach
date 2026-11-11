#!/usr/bin/env bash
# Starts the demo: backend (FastAPI, serves from bundle/) on :8000 and the built UI on :4173.
# Needs: uv, node 20+, npm. No raw data, database or MLflow.
set -euo pipefail
cd "$(dirname "$0")/.."

(cd backend && uv sync --locked)
(cd frontend && { [ -d node_modules ] || npm ci; } && npm run build)
(cd backend && uv run python -m credit_coach.bundle verify)

(cd backend && exec uv run uvicorn credit_coach.app:app --host 127.0.0.1 --port 8000) &
BACK=$!
trap 'kill "$BACK" 2>/dev/null || true' EXIT INT TERM

for _ in $(seq 1 120); do
  curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1 && break
  kill -0 "$BACK" 2>/dev/null || { echo "backend exited" >&2; exit 1; }
  sleep 1
done

echo "Demo: http://127.0.0.1:4173  (Ctrl+C to stop)"
cd frontend && npx vite preview --host 127.0.0.1 --port 4173 --strictPort
