# Coding Conventions

**Analysis Date:** 2026-03-14

## Naming Patterns

**Files:**
- Use snake_case for Python modules such as `credit-coach/src/credit_coach/model/train.py`
- Use `run_<workflow>.py` for CLI entry files in `credit-coach/src/credit_coach/cli/`
- Use `test_<behavior>.py` for pytest modules in `credit-coach/tests/`

**Functions:**
- Use snake_case for public and private functions
- Prefix internal helpers with `_` when they are module-private, for example `_safe_float`, `_gate_row`, `_configured_token_entries`

**Variables:**
- Use snake_case for locals and parameters
- Use UPPER_SNAKE_CASE for module constants such as `_STATUS_PRIORITY`

**Types:**
- Use PascalCase for Pydantic models and ORM-related classes such as `PlanRecord`, `TokenPolicyEntry`, and `RunContext`

## Code Style

**Formatting:**
- No dedicated formatter config was detected; follow the existing PEP 8 style already present in source files
- Imports are usually grouped as standard library, third-party, then internal modules
- Type hints are common and should be preserved

**Linting:**
- No explicit Ruff/Flake8/Black config was detected
- Conventions are enforced mostly by tests and by maintaining local style consistency

## Import Organization

**Order:**
1. Standard library imports
2. Third-party packages
3. Internal `credit_coach.*` imports

**Grouping:**
- Keep blank lines between import groups
- Multi-line imports are used when imported symbol counts are high, as in `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`

## Error Handling

**Patterns:**
- Throw or raise on invalid invariants, unsupported backends, or missing required artifacts
- Use safe extractor helpers like `_safe_float(...)` when building reports from partially populated artifacts
- Wrap DB writes in `with get_session()` so rollback happens automatically on errors

**Error Types:**
- `ValueError` and `RuntimeError` are used directly instead of a custom exception hierarchy
- Missing files/configs often fail fast with `FileNotFoundError`

## Logging

**Framework:**
- Standard library `logging`
- Major CLI modules call `logging.basicConfig(...)` and create module loggers

**Patterns:**
- Log at pipeline boundaries and around artifact/persistence setup
- Utilities stay quieter unless they create or save important resources

## Comments

**When to Comment:**
- Comments and docstrings explain why a module exists, not just what a line does
- Many files begin with long Turkish docstrings describing purpose and architecture
- Preserve this explanatory style when touching core modules

**Docstrings:**
- Public modules and functions often use docstrings with section-style explanations
- Keep these if modifying behavior; do not strip them for brevity

## Function Design

**Patterns:**
- Large orchestration files rely on many small helper functions rather than one deeply nested `main`
- Guard clauses and helper extraction are common in metric/gate code
- When a function needs many knobs, config dictionaries are preferred over long positional parameter lists

## Module Design

**Exports:**
- Modules export functions and classes directly; barrel modules are rare
- Keep business logic in domain modules and keep CLI files focused on orchestration where possible

**Data Contracts:**
- Use Pydantic models from `credit-coach/src/credit_coach/data/schema.py` when data is shared across modules
- Keep ORM-specific code in `credit-coach/src/credit_coach/storage/` rather than leaking it across the app

---
*Convention analysis: 2026-03-14*
*Update when patterns change*
