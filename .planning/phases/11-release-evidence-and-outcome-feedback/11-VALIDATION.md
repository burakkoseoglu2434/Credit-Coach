---
phase: 11
slug: release-evidence-and-outcome-feedback
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-15
---

# Phase 11 - Validation Strategy

> Per-phase validation contract for release-evidence hardening and outcome-feedback integration.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_telemetry_export.py tests/test_production_smoke.py tests/test_phase_experiment_suite.py tests/test_outcome_feedback.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_telemetry_export.py tests/test_production_smoke.py tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py tests/test_outcome_feedback.py tests/test_release_decision.py` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_telemetry_export.py tests/test_production_smoke.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_telemetry_export.py tests/test_production_smoke.py tests/test_phase_experiment_suite.py tests/test_outcome_feedback.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | OPS-01 | unit | `cd credit-coach && python -m pytest tests/test_telemetry_export.py tests/test_production_smoke.py` | ✅ | ⬜ pending |
| 11-01-02 | 01 | 1 | OPS-01 | regression | `cd credit-coach && python -m pytest tests/test_production_smoke.py tests/test_release_decision.py` | ✅ | ⬜ pending |
| 11-02-01 | 02 | 2 | OPS-02 | contract | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_production_smoke.py` | ✅ | ⬜ pending |
| 11-02-02 | 02 | 2 | OPS-02 | integration | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py tests/test_production_smoke.py` | ✅ | ⬜ pending |
| 11-03-01 | 03 | 3 | OPS-03 | unit | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py` | ✅ | ⬜ pending |
| 11-03-02 | 03 | 3 | OPS-03 | integration | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_phase_experiment_suite.py tests/test_production_smoke.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_telemetry_export.py` - extend exporter-health and file-output assertions before production-profile enforcement changes
- [x] `credit-coach/tests/test_production_smoke.py` - protect fail-closed telemetry semantics and broad-rollout gating behavior
- [x] `credit-coach/tests/test_phase_experiment_suite.py` - extend release-pack and stable-artifact reference assertions
- [x] `credit-coach/tests/test_challenger_matrix_selection.py` - ensure evidence-pack references stay aligned across seeded challenger outputs
- [x] `credit-coach/tests/test_outcome_feedback.py` - extend business-proxy reporting and release-review linkage assertions
- [x] `credit-coach/tests/test_release_decision.py` - preserve Phase 8 release precedence while telemetry and outcome evidence remain additive

---

## Manual-Only Verifications

One human scan is still useful after execution:

- confirm production-profile telemetry behavior reads as fail-closed and never silently downgrades to best-effort broad rollout
- confirm degraded telemetry also blocks pilot eligibility rather than only broad rollout
- confirm release evidence packs point to stable `tables/`-relative machine-readable artifacts rather than copying large payloads into markdown
- confirm outcome-feedback summaries clearly describe business-impact proxies without overstating causal certainty, and fall back cleanly when the control baseline is missing
- confirm the review opens with evidence status and keeps the locked Phase 11 section order

All core behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers telemetry, release-pack, and outcome-feedback seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-15
