# Codebase Structure

**Analysis Date:** 2026-03-14

## Directory Layout

```text
Credit-Coach/
├── .planning/                      # GSD planning docs and imported legacy material
├── .codex/                         # GSD/Codex skills, workflows, templates, agents
├── credit-coach/                   # Main Python application
│   ├── configs/                    # YAML configs and experiment variants
│   ├── data/                       # Sample/source datasets
│   ├── src/credit_coach/           # Application package
│   ├── tests/                      # Pytest suite
│   ├── artifacts/                  # Generated run outputs (created by pipelines)
│   ├── pyproject.toml              # Package metadata and pytest settings
│   └── README.md                   # Project usage and operational notes
└── .DS_Store                       # Local OS metadata
```

## Directory Purposes

**`credit-coach/src/credit_coach/`:**
- Purpose: all implementation code
- Contains: Python modules grouped by domain
- Key files: `cli/run_batch_recourse_eval.py`, `model/train.py`, `storage/repository.py`, `data/schema.py`
- Subdirectories: `api/`, `app/`, `causality/`, `cli/`, `coaching/`, `data/`, `evaluation/`, `macro/`, `model/`, `ops/`, `policy/`, `portfolio/`, `recourse/`, `retraining/`, `safety/`, `storage/`, `utils/`, `xai/`

**`credit-coach/configs/`:**
- Purpose: runtime behavior and experiment tuning
- Contains: base configs plus many variant files in `credit-coach/configs/experiments/`
- Key files: `features_48.yaml`, `model.yaml`, `recourse.yaml`, `monitoring.yaml`, `kpi_contract.yaml`, `security.yaml`

**`credit-coach/tests/`:**
- Purpose: centralized pytest suite
- Contains: `test_*.py` modules and `conftest.py`
- Key files: `test_production_smoke.py`, `test_model_pipeline.py`, `test_recourse_feasibility.py`, `test_auth.py`

**`credit-coach/data/`:**
- Purpose: sample input data
- Contains: CSV sample dataset
- Key files: `credit-coach/data/sample/lending_club_sample_2000.csv`

**`.planning/`:**
- Purpose: GSD project memory, roadmap, requirements, and codebase map
- Contains: root planning docs plus `archive/`, `research/`, `references/`, and `codebase/`

## Key File Locations

**Entry Points:**
- `credit-coach/src/credit_coach/cli/run_train.py` - model training pipeline
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py` - highest-complexity batch evaluation pipeline
- `credit-coach/src/credit_coach/cli/run_production_smoke.py` - release-gate decision pipeline
- `credit-coach/src/credit_coach/app/streamlit_app.py` - local interactive demo

**Configuration:**
- `credit-coach/pyproject.toml` - package metadata and pytest defaults
- `credit-coach/.env.example` - sample environment variables
- `credit-coach/configs/*.yaml` - operational configs

**Core Logic:**
- `credit-coach/src/credit_coach/model/` - training, prediction, registry
- `credit-coach/src/credit_coach/recourse/` - candidate generation, DiCE integration, feasibility
- `credit-coach/src/credit_coach/coaching/` - plan selection and sequential coaching
- `credit-coach/src/credit_coach/evaluation/` - fairness, metrics, benchmark logic
- `credit-coach/src/credit_coach/safety/` - validation and statistical checks
- `credit-coach/src/credit_coach/storage/` - DB engine, ORM, repository

**Testing:**
- `credit-coach/tests/` - all automated tests
- `credit-coach/tests/conftest.py` - shared fixtures

**Documentation:**
- `credit-coach/README.md` - developer-facing usage
- `.planning/` - planning and migrated historical docs

## Naming Conventions

**Files:**
- snake_case Python modules such as `run_batch_recourse_eval.py`
- pytest files use `test_*.py`
- YAML config files use snake_case and descriptive suffixes

**Directories:**
- snake_case package directories inside `credit-coach/src/credit_coach/`
- flat domain folders rather than feature slices

**Special Patterns:**
- CLI modules follow `run_<workflow>.py`
- artifact outputs are grouped per run under `artifacts/runs/<run_id>/`

## Where to Add New Code

**New Feature:**
- Primary code: put domain logic into the matching package under `credit-coach/src/credit_coach/`
- Tests: add a `credit-coach/tests/test_<feature>.py` file or extend the nearest existing test module
- Config if needed: add a focused YAML file under `credit-coach/configs/`

**New CLI Workflow:**
- Definition: `credit-coach/src/credit_coach/cli/run_<name>.py`
- Supporting domain code: domain package, not inside the CLI file unless it is truly orchestration-only
- Tests: `credit-coach/tests/test_<name>.py`

**Utilities:**
- Shared helpers: `credit-coach/src/credit_coach/utils/`
- Shared schemas: `credit-coach/src/credit_coach/data/schema.py` or a nearby data module

## Special Directories

**`credit-coach/artifacts/`:**
- Purpose: generated run outputs and evidence
- Source: auto-created by pipeline execution
- Committed: generally no; treat as generated runtime data

**`credit-coach/configs/experiments/`:**
- Purpose: large library of experiment variants and tuning profiles
- Source: hand-authored config iterations
- Committed: yes

---
*Structure analysis: 2026-03-14*
*Update when directory structure changes*
