# Technology Stack

**Analysis Date:** 2026-03-14

## Languages

**Primary:**
- Python 3.11+ - All application code under `credit-coach/src/credit_coach/` and all automated tests under `credit-coach/tests/`

**Secondary:**
- YAML - Runtime and experiment configuration in `credit-coach/configs/*.yaml`
- Markdown - Developer and operational documentation in `credit-coach/README.md` and `.planning/`

## Runtime

**Environment:**
- CPython 3.11+ - Declared in `credit-coach/pyproject.toml`
- Local CLI/runtime flow rather than a long-running web service

**Package Manager:**
- `pip` / setuptools editable install - documented in `credit-coach/README.md`
- Lockfile: Not detected (`requirements.txt` exists, but no Poetry/Pipenv lockfile)

## Frameworks

**Core:**
- scikit-learn - baseline/fallback model training in `credit-coach/src/credit_coach/model/train.py`
- XGBoost - optional production-grade model backend in `credit-coach/src/credit_coach/model/train.py`
- Pydantic v2 - schema contracts in `credit-coach/src/credit_coach/data/schema.py`
- SQLAlchemy 2.x - product-state persistence in `credit-coach/src/credit_coach/storage/db.py` and `credit-coach/src/credit_coach/storage/repository.py`
- Streamlit - offline demo UI in `credit-coach/src/credit_coach/app/streamlit_app.py`

**Testing:**
- pytest - all tests configured via `credit-coach/pyproject.toml`

**Build/Dev:**
- setuptools legacy backend - package build defined in `credit-coach/pyproject.toml`

## Key Dependencies

**Critical:**
- `pandas>=2.1` - table-oriented artifact generation and KPI summaries across CLI pipelines
- `numpy>=1.26` - numerical operations in evaluation and model flows
- `scikit-learn>=1.4` - logistic regression fallback and model evaluation
- `xgboost>=2.0` - optional boosted-tree backend with deterministic training guardrails
- `shap>=0.45` - local explanation generation in `credit-coach/src/credit_coach/xai/`
- `dice-ml>=0.11` - counterfactual baseline generation in `credit-coach/src/credit_coach/recourse/dice_baseline.py`

**Infrastructure:**
- `pyyaml>=6.0` - config-first runtime behavior across `credit-coach/configs/`
- `sqlalchemy>=2.0` - SQLite-backed state store and audit persistence
- `pyarrow>=14.0` - data pipeline and artifact serialization support

## Configuration

**Environment:**
- Environment variables come from `.env` plus direct shell exports; example file at `credit-coach/.env.example`
- Security and auth behavior depend on vars such as `CREDIT_COACH_API_TOKEN`, `CREDIT_COACH_API_TOKENS`, `CREDIT_COACH_API_KEYS_JSON`, `CREDIT_COACH_ALLOW_INSECURE_API`, and `DB_URL`
- Model backend switching uses `CREDIT_COACH_FORCE_BACKEND` and `CREDIT_COACH_ALLOW_XGB` in `credit-coach/src/credit_coach/model/train.py`

**Build:**
- `credit-coach/pyproject.toml` - package metadata, dependencies, pytest config
- `credit-coach/requirements.txt` - alternate dependency installation path
- `credit-coach/configs/*.yaml` - feature contract, model, recourse, monitoring, safety, governance, KPI, and experiment configs

## Platform Requirements

**Development:**
- Any OS that can run Python 3.11 and SQLite
- File-system access for `artifacts/runs/<run_id>/` output and local YAML configs

**Production:**
- Current code targets batch/CLI execution plus local demo usage rather than a packaged deployment platform
- Telemetry export supports HTTP push or file output from `credit-coach/src/credit_coach/ops/telemetry.py`

---
*Stack analysis: 2026-03-14*
*Update after major dependency changes*
