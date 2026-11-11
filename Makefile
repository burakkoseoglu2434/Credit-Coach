.PHONY: openapi types lint test check demo report

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

demo:
	./scripts/demo.sh

report:
	cd backend && uv run python -m credit_coach.portfolio_report
