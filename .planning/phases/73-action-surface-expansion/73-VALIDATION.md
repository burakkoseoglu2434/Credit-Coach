---
phase: 73
slug: action-surface-expansion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-14
---

# Phase 73 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4 |
| **Config file** | none found at repo root for credit-coach (relies on `PYTHONPATH=src` convention, e.g. `cd credit-coach && PYTHONPATH=src python3 -m pytest ...`) |
| **Quick run command** | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -q` |
| **Full suite command** | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/ -q -k "recourse or recoverab or cohort or rendering"` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -q`
- **After every plan wave:** Run `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/ -q -k "recourse or recoverab or cohort or rendering"`
- **Before `/gsd-verify-work`:** Full suite must be green, plus an n=500 (minimum) cohort re-run comparing pre/post Phase 73 trust counters and `action_type_distribution_table`.
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 73-01-01 | 01 | 0 | SURF-01 | T-73-01 | `full`-tier customer with ≥2 distinct-family rankable paths surfaces 2 actions (`selected_action_count == 2`, `selected_secondary_action_present == 1`) | unit | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -k top_k -x` | ❌ W0 | ⬜ pending |
| 73-01-02 | 01 | 0 | SURF-01 | T-73-01 | `full`-tier customer with only 1 rankable path (or no distinct-family alternative) surfaces exactly 1 action, unchanged | unit | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -k top_k -x` | ❌ W0 | ⬜ pending |
| 73-01-03 | 01 | 1 | SURF-02 | T-73-01 | Action #2 (when present) uses an existing supported `action_family`, never a synthesized/new semantic | unit | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -k secondary -x` | ❌ W0 | ⬜ pending |
| 73-01-04 | 01 | 1 | SURF-02 | T-73-02 | Action #2 excludes `action_owner == "institution"` candidates | unit | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -k institution -x` | ❌ W0 | ⬜ pending |
| 73-01-05 | 01 | 1 | TRUST-04 | T-73-01 | Action #2's narrative text comes from `customer_summary`/`operator_summary` of the alternative path, never invented claims | unit | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -k secondary_narrative -x` | ❌ W0 | ⬜ pending |
| 73-01-06 | 01 | 1 | TRUST-01/02/03 | T-73-02 | Existing 6/6 `test_recourse_gate_relaxation.py` tests and `assisted_full`/`limited` behavior remain unaffected | regression | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -q` | ✅ exists | ⬜ pending |
| 73-02-01 | 02 | 1 | SURF-03 | T-73-01 | Cohort evaluation emits `action_type_distribution_table` with non-empty family/type distributions for `full`-tier population | integration | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/ -q -k "action_type_distribution" -x` | ❌ W0 | ⬜ pending |
| 73-02-02 | 02 | 2 | TRUST-01/02/03 | T-73-02 | Trust counters (`selected_invalid_winner_count`, `selected_surface_drift_count`, `operator_packet_contradiction_count`) remain 0 after top-k=2 change on n=500 cohort re-run | integration | `cd credit-coach && PYTHONPATH=src python3 -m run_v24_cohort_evaluation ...` (re-run Phase 72's evidence pipeline, diff trust counters against `72-REPORT.md` baseline) | ✅ existing pipeline | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `credit-coach/tests/test_recourse_gate_relaxation.py` (or new `tests/test_recourse_action_surface_expansion.py`) — new test functions for top-k=2 selection (SURF-01), institutional-exclusion (SURF-02), and secondary narrative sourcing (TRUST-04), extending the existing `_roadmap()` fixture builder with a `"paths": [...]` key.
- [ ] Test(s) for `action_type_distribution_table` construction in `cohort_evidence.py` / `run_v24_cohort_evaluation.py`, following the existing `selected_path_distribution_table` test pattern.
- [ ] Repo-wide grep for `selected_action_count` usages outside `run_recourse.py` and `run_v24_cohort_evaluation.py` to confirm no hidden `<= 1` assumptions.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
