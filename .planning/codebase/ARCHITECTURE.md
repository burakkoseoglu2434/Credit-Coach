# Architecture

**Analysis Date:** 2026-03-14

## Pattern Overview

**Overall:** Monolithic Python analytics and decisioning application built around CLI pipelines, shared domain modules, and file-based experiment artifacts.

**Key Characteristics:**
- Most execution begins from CLI entry modules in `credit-coach/src/credit_coach/cli/`
- Runtime behavior is config-first; YAML files under `credit-coach/configs/` steer nearly every pipeline
- State is split between immutable-ish run artifacts on disk and mutable product/audit state in SQLite
- Business logic is organized by domain packages rather than framework layers

## Layers

**Entry Layer:**
- Purpose: parse arguments, load configs, choose artifacts, and orchestrate workflows
- Contains: CLI modules such as `credit-coach/src/credit_coach/cli/run_train.py`, `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`, and `credit-coach/src/credit_coach/cli/run_production_smoke.py`
- Depends on: all downstream domain modules
- Used by: shell commands and automation scripts

**Domain Logic Layer:**
- Purpose: implement modeling, recourse generation, safety validation, fairness, macro stress, and policy logic
- Contains: `credit-coach/src/credit_coach/model/`, `recourse/`, `safety/`, `evaluation/`, `macro/`, `policy/`, `coaching/`, `xai/`
- Depends on: shared schema/config helpers and some storage utilities
- Used by: CLI entry points and Streamlit demo

**Contract Layer:**
- Purpose: keep data shapes explicit across the codebase
- Contains: Pydantic models in `credit-coach/src/credit_coach/data/schema.py`
- Depends on: Pydantic and utility time helpers
- Used by: recourse, storage, evaluation, and audit flows

**Persistence Layer:**
- Purpose: save product state and hash-chained audit history
- Contains: `credit-coach/src/credit_coach/storage/db.py`, `models.py`, `repository.py`
- Depends on: SQLAlchemy and schema models
- Used by: CLI workflows that persist runs, decisions, and audit events

**Artifact Layer:**
- Purpose: create reproducible run directories and write outputs
- Contains: `credit-coach/src/credit_coach/utils/run_context.py` plus many CLI writers
- Depends on: local filesystem and YAML/JSON serializers
- Used by: every long-running pipeline

## Data Flow

**CLI Pipeline Execution:**

1. A command such as `python -m credit_coach.cli.run_batch_recourse_eval` starts from `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
2. The CLI parses args and loads YAML configs via helpers such as `load_config(...)`
3. A run context is created in `credit-coach/src/credit_coach/utils/run_context.py`, producing a unique run directory
4. Domain modules perform prediction, recourse generation, validation, fairness, and telemetry calculations
5. Summaries and tables are written under `artifacts/runs/<run_id>/`
6. Some workflows also persist structured state and audit events through `credit-coach/src/credit_coach/storage/repository.py`

**Production Smoke Flow:**

1. `credit-coach/src/credit_coach/cli/run_production_smoke.py` locates the latest batch, benchmark, monitoring, fairness, and telemetry artifacts
2. It applies KPI thresholds from `credit-coach/src/credit_coach/ops/kpi_contract.py`
3. It emits gate rows that decide GO/FAIL outcomes

**State Management:**
- Durable execution evidence: filesystem artifacts in `credit-coach/artifacts/runs/`
- Product/audit state: SQLite or another SQLAlchemy-supported database from `DB_URL`
- Config state: YAML files under `credit-coach/configs/`

## Key Abstractions

**RunContext:**
- Purpose: isolate one pipeline execution and snapshot its config
- Examples: `create_run_context(...)` in `credit-coach/src/credit_coach/utils/run_context.py`
- Pattern: lightweight factory plus filesystem-oriented object

**PlanRecord / PlanAction:**
- Purpose: define the shape of recourse plans and actions
- Examples: `credit-coach/src/credit_coach/data/schema.py`
- Pattern: Pydantic domain contract

**Repository Functions:**
- Purpose: hide ORM details and append audit events on writes
- Examples: `save_plan(...)`, `save_model_run(...)` in `credit-coach/src/credit_coach/storage/repository.py`
- Pattern: functional repository over SQLAlchemy sessions

## Entry Points

**CLI Commands:**
- Location: `credit-coach/src/credit_coach/cli/*.py`
- Triggers: shell execution via `python -m credit_coach.cli.<module>`
- Responsibilities: argument parsing, config composition, workflow orchestration, artifact writing

**Streamlit Demo:**
- Location: `credit-coach/src/credit_coach/app/streamlit_app.py`
- Triggers: Streamlit app launch
- Responsibilities: interactive local demonstration of the system

## Error Handling

**Strategy:** fail fast on invalid configuration or missing artifacts, with helper functions returning safe defaults only where partial metrics are acceptable.

**Patterns:**
- Validation functions often raise directly for unsupported values, such as backend selection in `credit-coach/src/credit_coach/model/train.py`
- Metric extractors use `_safe_float(...)` and similar helpers to keep report assembly from crashing on sparse data
- Storage operations use `get_session()` context management in `credit-coach/src/credit_coach/storage/db.py` for automatic rollback

## Cross-Cutting Concerns

**Logging:**
- Python `logging.basicConfig(...)` appears in major CLI modules

**Validation:**
- Pydantic validates domain records
- KPI and safety gates validate outcomes after generation

**Authentication:**
- Custom bearer-token and scope checks live in `credit-coach/src/credit_coach/api/auth.py`

---
*Architecture analysis: 2026-03-14*
*Update when major patterns change*
