# Phase 73: Action Surface Expansion - Pattern Map

**Mapped:** 2026-06-14
**Files analyzed:** 4 (3 modified, 1 new test module)
**Analogs found:** 4 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|-----------------|---------------|
| `credit-coach/src/credit_coach/cli/run_recourse.py` (modify: `_apply_recourse_gate_to_roadmap`, `_build_selected_surface_projection`, new helper functions) | service/transform | transform (CRUD-like roadmap mutation) | itself (existing functions in same file) | exact |
| `credit-coach/src/credit_coach/evaluation/cohort_evidence.py` (modify: `build_phase60_evidence_summary`, `render_phase60_evidence_markdown`, `write_phase60_evidence_artifacts`) | service/transform | batch (aggregation over packages) | itself — `selected_path_distribution_table` pattern (lines 450, 465, 609, 621, 633) | exact |
| `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py` (modify: per-customer row construction, package builder feeding `cohort_evidence.py`) | service/transform | batch | existing `selected_path_distribution` package builder (same file) | exact |
| `credit-coach/tests/test_recourse_gate_relaxation.py` (add new test functions) OR new `tests/test_recourse_action_surface_expansion.py` | test | transform | `tests/test_recourse_gate_relaxation.py` (existing `_roadmap()` fixture + 6 tests) | exact |

## Pattern Assignments

### `credit-coach/src/credit_coach/cli/run_recourse.py` (service, transform)

**Analog:** same file — `_apply_recourse_gate_to_roadmap` (lines 908-1037) and `_build_selected_surface_projection` (lines 1286-1354)

**Imports pattern** — `action_space` is not currently imported in `run_recourse.py`; add:
```python
from credit_coach.recourse.action_space import ACTION_CATALOG, LEGACY_ACTION_FAMILY_BY_ACTION_KEY
```

**Gate seam — where top-k=2 branch goes** (lines 970-971):
```python
if _safe_text(gate.get("recourse_mode")) != "limited":
    return _build_selected_surface_projection(out)
```
Insert the `recourse_mode == "full"` top-k branch immediately before this `return`, computing the secondary path and stashing it on `summary` (or `out`) so `_build_selected_surface_projection` can read it. Do NOT touch the `assisted_full` block above (lines 940-968) or the `limited` block below (lines 973+).

**Source of `out["paths"]`** — already attached pre-gate via `_attach_path_summary_to_roadmap` (lines 410-439):
```python
out["paths"] = [record.model_dump(mode="json") for record in path_records]
```
Each entry has `path_rank`, `action_keys`, `rankable_flag`, `selected_path_flag`, `path_type`, `path_id`, `customer_summary`/`operator_summary` (dicts with `tr`/`en`).

**Localized payload helpers to reuse** (lines 1260-1283):
```python
def _localized_projection_payload(payload: Any) -> dict[str, str] | None:
    if isinstance(payload, dict):
        tr = _safe_text(payload.get("tr"))
        en = _safe_text(payload.get("en"))
        if tr or en:
            return {"tr": tr or en, "en": en or tr}
    text = _safe_text(payload)
    if text:
        return {"tr": text, "en": text}
    return None


def _localized_projection_text(payload: Any, *, locale: str = "en") -> str | None:
    normalized = _localized_projection_payload(payload)
    if not normalized:
        return None
    primary = _safe_text(normalized.get(locale))
    if primary:
        return primary
    secondary = "tr" if locale == "en" else "en"
    return _safe_text(normalized.get(secondary)) or None
```
Apply identically to `secondary_path.get("customer_summary")` for action #2's narrative — same renderer as action #1, satisfies TRUST-04.

**Core additive projection pattern** (lines 1333-1352, `_build_selected_surface_projection`'s `summary.update({...})` block) — extend with new `selected_secondary_*` keys using the same `.update()` style; never remove/overwrite existing keys (`selected_recommendation_text`, `selected_plan_id`, `best_plan_id`, `selected_action_count` bump is explicitly allowed per RESEARCH.md Pattern 2/Pitfall 3).

**Error handling / defensive access pattern** — file-wide convention is `.get()` with defaults plus `_safe_text`/`_safe_int`/`_safe_float` helpers (used throughout `_apply_recourse_gate_to_roadmap`, e.g. line 941 `_safe_text(summary.get("pre_gate_selected_path_type")).lower()`). New code must use `out.get("paths", [])` (never `out["paths"]`) per Pitfall 4 — handles fixtures/test roadmaps that omit `paths` entirely.

**Selection helper to add** (new functions, place near `_localized_projection_payload`):
```python
def _action_family_for_key(action_key: str) -> str | None:
    return LEGACY_ACTION_FAMILY_BY_ACTION_KEY.get(str(action_key or "").strip())


def _is_institutional_action(action_key: str) -> bool:
    template = ACTION_CATALOG.get(str(action_key or "").strip())
    return bool(template and template.action_owner == "institution")


def _select_secondary_action_for_full_mode(roadmap: dict, *, primary_action_key: str) -> dict | None:
    primary_family = _action_family_for_key(primary_action_key)
    paths = roadmap.get("paths", [])
    if not isinstance(paths, list):
        return None
    candidates = sorted(
        (p for p in paths if isinstance(p, dict)),
        key=lambda p: int(p.get("path_rank") or 999999),
    )
    for path in candidates:
        if not bool(path.get("rankable_flag", False)):
            continue
        if bool(path.get("selected_path_flag", False)):
            continue
        action_keys = path.get("action_keys") or []
        if not action_keys:
            continue
        candidate_key = str(action_keys[0])
        if _is_institutional_action(candidate_key):
            continue
        candidate_family = _action_family_for_key(candidate_key)
        if candidate_family and candidate_family != primary_family:
            return path
    return None
```

---

### `credit-coach/src/credit_coach/evaluation/cohort_evidence.py` (service, batch)

**Analog:** `selected_path_distribution_table` plumbing — three sites:

**1. Summary builder** (line 450, inside `build_phase60_evidence_summary`):
```python
selected_path_distribution_table = [dict(pkg.get("selected_path_distribution", {}) or {}) for pkg in package_list]
```
and (line 465) added to the returned dict as `"selected_path_distribution_table": selected_path_distribution_table,`.

Add an analogous line for the new table:
```python
action_type_distribution_table = [dict(pkg.get("action_type_distribution", {}) or {}) for pkg in package_list]
```
plus `"action_type_distribution_table": action_type_distribution_table,` in the returned dict (line ~465-470).

**2. Markdown rendering pattern** (lines 567-580, "## Recourse Gate" section) — use `json.dumps(dict(row.get(...), {}) or {}), ensure_ascii=False, sort_keys=True)` for dict-valued distribution fields:
```python
lines.extend(["", "## Recourse Gate"])
recourse_gate_rows = list(summary.get("recourse_gate_table", []) or [])
if recourse_gate_rows:
    for row in recourse_gate_rows:
        lines.append(
            "- "
            f"{_safe_str(row.get('population'), 'unknown')}: "
            f"recourse_mode_distribution={json.dumps(dict(row.get('recourse_mode_distribution', {}) or {}), ensure_ascii=False, sort_keys=True)}, ..."
        )
else:
    lines.append("- n/a")
```
Follow this exact shape for a new "## Action Type Distribution" section reporting `action_type_distribution_table` (and optionally `action1_family_distribution` / `action2_family_distribution` per RESEARCH.md Open Question 2).

**3. Artifact writer** (lines 609, 621, 633, inside `write_phase60_evidence_artifacts`):
```python
selected_csv = output_root / f"{prefix}_selected_path_distribution_table.csv"
...
pd.DataFrame(list(summary.get("selected_path_distribution_table", []) or [])).to_csv(selected_csv, index=False)
...
"selected_path_distribution_table_csv": selected_csv.name,
```
Add analogous `action_type_csv = output_root / f"{prefix}_action_type_distribution_table.csv"`, the `to_csv` call, and the returned-mapping entry `"action_type_distribution_table_csv": action_type_csv.name`.

---

### `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py` (service, batch)

**Analog:** package builder that produces `pkg["selected_path_distribution"]` (the input consumed by `cohort_evidence.py` line 450). Locate this builder via the per-customer aggregation around `_aggregate_metrics` (lines 779-940+) and customer row construction (lines 1638-1845) referenced in RESEARCH.md.

**Pattern:** for each `full`-tier customer row, read the new additive `selected_secondary_action_family` / `selected_secondary_action_present` fields off `roadmap_summary` (produced by `run_recourse.py`'s projection) and fold them into a population-level `action_type_distribution` dict alongside the existing per-row `selected_path_type` -> `selected_path_distribution` aggregation — mirror whatever counter/Counter-based aggregation produces `selected_path_distribution` today (grep `selected_path_distribution` in this file to find the exact counter pattern before implementing).

**Trust-counter caution:** do not modify `selected_invalid_winner_count`, `selected_surface_drift_count`, `operator_packet_contradiction_count` computations — these must read action #1 fields only, unchanged (TRUST-01/02/03).

---

### `credit-coach/tests/test_recourse_gate_relaxation.py` (test, transform)

**Analog:** existing `_roadmap()` fixture helper (lines 8-33) and the 6 existing test functions (e.g. `test_assisted_full_routing_and_pruning_surfaces_exactly_one_allowlisted_step`, line 36).

**Fixture extension needed:** `_roadmap()` currently does not include a `"paths"` key (lines 18-33). New tests for top-k=2 must either:
- extend `_roadmap()` with an optional `paths: list[dict] | None = None` kwarg defaulting to `[]`, added as `"paths": paths or []` in the returned dict, OR
- construct the roadmap dict inline with `"paths": [...]` for `full`-mode tests.

**Test invocation pattern** (lines 36-86 style):
```python
def test_full_mode_surfaces_secondary_action_from_distinct_family_path() -> None:
    out = _apply_recourse_gate_to_roadmap(
        _roadmap(
            selected_path_type="customer_only",
            phases=[...],
            narrative_steps=[...],
            recourse_gate_config={...},
            # extended: paths=[...]
        )
    )
    summary = out["summary"]
    assert summary["selected_secondary_action_present"] == 1
    assert summary["selected_action_count"] == 2
```

Place new tests either appended to this file or in a new sibling file `tests/test_recourse_action_surface_expansion.py` importing `_apply_recourse_gate_to_roadmap` the same way (line 5):
```python
from credit_coach.cli.run_recourse import _apply_recourse_gate_to_roadmap
```

---

## Shared Patterns

### Defensive dict access (`.get()` with defaults)
**Source:** `credit_coach/cli/run_recourse.py` throughout `_apply_recourse_gate_to_roadmap`/`_build_selected_surface_projection`, e.g.:
```python
out.get("paths", [])
summary.get("selected_action_count", summary.get("best_action_count", len(steps)))
```
**Apply to:** All new selection/projection code — never use `roadmap["paths"]` (Pitfall 4).

### Additive `summary.update({...})` projection
**Source:** `_build_selected_surface_projection`, lines 1333-1352
**Apply to:** All new `selected_secondary_*` fields — append new keys via `.update()`, never remove or rewrite existing `selected_recommendation_*` / `selected_plan_id` / `best_plan_id` keys (TRUST-04).

### Action family / owner classification (single source of truth)
**Source:** `credit_coach/recourse/action_space.py` lines 59-71 (`LEGACY_ACTION_FAMILY_BY_ACTION_KEY`) and lines 178+ (`ACTION_CATALOG`, `ActionTemplate.action_owner`)
**Apply to:** `run_recourse.py` selection helper — `_action_family_for_key()` and `_is_institutional_action()` must read from these tables, never a parallel mapping.

### Dict-valued distribution table + CSV/MD/JSON triple-write
**Source:** `credit_coach/evaluation/cohort_evidence.py` — `selected_path_distribution_table` appears in three places: `build_phase60_evidence_summary` (line 450/465), `render_phase60_evidence_markdown` (lines 567-580 style for dict fields via `json.dumps(..., sort_keys=True)`), and `write_phase60_evidence_artifacts` (lines 609/621/633).
**Apply to:** New `action_type_distribution_table` — replicate all three sites with parallel naming.

## No Analog Found

None — all 4 files/areas have exact analogs within the same modules (this phase is purely additive within mature, well-patterned code).

## Metadata

**Analog search scope:** `credit-coach/src/credit_coach/cli/`, `credit-coach/src/credit_coach/evaluation/`, `credit-coach/src/credit_coach/recourse/`, `credit-coach/tests/`
**Files scanned:** `run_recourse.py`, `cohort_evidence.py`, `action_space.py`, `test_recourse_gate_relaxation.py`, `run_v24_cohort_evaluation.py` (grep only)
**Pattern extraction date:** 2026-06-14
