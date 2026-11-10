.PHONY: openapi types lint test check

openapi:
	cd backend && PYTHONPATH=src uv run python -m credit_coach.export_openapi ../frontend/openapi.json

types: openapi
	cd frontend && npm run gen:types

lint:
	cd backend && uv run ruff check .

test:
	cd backend && uv run pytest -q

check: lint test types
	cd frontend && npm run typecheck
