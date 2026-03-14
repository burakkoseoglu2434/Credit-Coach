# Testing Patterns

**Analysis Date:** 2026-03-14

## Test Framework

**Runner:**
- `pytest` configured in `credit-coach/pyproject.toml`
- Default options: `-v --tb=short`

**Assertion Library:**
- Built-in pytest assertions
- Common patterns include direct `assert`, `pytest.raises`, and pandas-based checks

**Run Commands:**
```bash
cd credit-coach && pytest
cd credit-coach && pytest tests/test_production_smoke.py
cd credit-coach && pytest -q
```

## Test File Organization

**Location:**
- All tests live in the dedicated tree `credit-coach/tests/`

**Naming:**
- Files use `test_<topic>.py`
- Tests inside files use descriptive `test_<behavior>()` names

**Structure:**
```text
credit-coach/tests/
  conftest.py
  test_auth.py
  test_model_pipeline.py
  test_production_smoke.py
  test_recourse_feasibility.py
  ...
```

## Test Structure

**Suite Organization:**
```python
def test_build_smoke_gate_rows_passes():
    batch_summary = {...}
    rows = build_smoke_gate_rows(...)
    out = pd.DataFrame(rows)
    assert len(out) == 8
    assert (out["status"] == "PASS").all()
```

**Patterns:**
- Tests are usually flat functions rather than nested classes
- Arrange/act/assert structure is common even when not commented explicitly
- Helper factories sometimes appear at the top of the file, such as `_args(...)` in `credit-coach/tests/test_production_smoke.py`

## Mocking

**Framework:**
- pytest fixtures plus `monkeypatch`

**Patterns:**
```python
def test_verify_token_with_configured_token(monkeypatch):
    monkeypatch.setenv("CREDIT_COACH_API_TOKEN", "secret-token")
    assert verify_token("secret-token") is True
```

**What to Mock:**
- Environment variables
- Temporary database locations
- Config-dependent runtime behavior

**What NOT to Mock:**
- Pure metric helpers and domain calculations when real execution is cheap

## Fixtures and Factories

**Test Data:**
- Shared fixtures live in `credit-coach/tests/conftest.py`
- Example fixtures: `feature_list_48`, `features_config`, `temp_db_url`, `sample_features`

**Location:**
- Global reusable fixtures go in `credit-coach/tests/conftest.py`
- File-local helpers stay inside the test module

## Coverage

**Requirements:**
- No explicit coverage threshold was detected
- Practical expectation is broad regression coverage across modeling, recourse, security, and smoke-gate workflows

**Scope clues from current suite:**
- Auth and rate limiting
- Model pipeline and backend selection
- DiCE, recourse feasibility, and sequential coaching
- Fairness, telemetry, production smoke, and challenger evaluation

## Test Types

**Unit Tests:**
- Most files are unit or focused integration tests around a single module or workflow contract

**Integration Tests:**
- Several CLI-facing modules are tested through helper functions and generated row outputs instead of subprocess execution

**E2E Tests:**
- Browser or end-to-end UI tests were not detected

## Common Patterns

**Async Testing:**
- Not common in the files reviewed; most logic is synchronous

**Error Testing:**
```python
with pytest.raises(FileNotFoundError):
    load_config("missing.yaml")
```

**DataFrame Validation:**
- KPI and smoke tests often convert result rows into `pandas.DataFrame` for assertions

---
*Testing analysis: 2026-03-14*
*Update when test patterns change*
