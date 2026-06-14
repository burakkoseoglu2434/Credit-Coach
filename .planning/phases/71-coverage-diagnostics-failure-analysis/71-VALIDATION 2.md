---
phase: 71
slug: 71-coverage-diagnostics-failure-analysis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 71 — Validation Strategy

> Per-phase validation contract for emitting additive coverage diagnostics without changing shipped gating/selection semantics.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + lightweight artifact checks |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_coverage_diagnostics.py -q` |
| **Full suite command** | `cd credit-coach && PYTHONPATH=src python3 -m pytest -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run Quick run command
- **After every plan wave:** Run Full suite command
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 71-01-01 | 01 | 1 | COV-01 | compile | `cd credit-coach && PYTHONPATH=src python3 -m compileall -q src` | ✅ | ⬜ pending |
| 71-01-02 | 01 | 1 | COV-01 | cli | `cd credit-coach && PYTHONPATH=src python3 -m credit_coach.cli.run_v27_coverage_diagnostics --run_dir artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42 --gap_closure_epsilon 0.05 >/dev/null && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42/coverage_diagnostics/coverage_diagnostic_summary.json && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42/coverage_diagnostics/coverage_diagnostic_customer_breakdown.csv && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42/coverage_diagnostics/coverage_reason_frequency.csv && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42/coverage_diagnostics/empty_state_decomposition.json` | ❌ W0 | ⬜ pending |
| 71-01-03 | 01 | 1 | COV-01 | regression | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 71-01-04 | 01 | 1 | COV-01 | unit | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_coverage_diagnostics.py -q` | ❌ W0 | ⬜ pending |
| 71-02-01 | 02 | 2 | COV-02 | artifact-check | `test -f credit-coach/artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/W2a_large_n3000_seed42/customer_level_analysis.csv && test -f credit-coach/artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/W2a_large_n3000_seed42/cohort_metrics.json` | ✅ | ⬜ pending |
| 71-02-02 | 02 | 2 | COV-03 | integration | `cd credit-coach && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/W2a_large_n3000_seed42/coverage_diagnostics/coverage_diagnostic_summary.json && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/W2a_large_n3000_seed42/coverage_diagnostics/coverage_diagnostic_customer_breakdown.csv && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/W2a_large_n3000_seed42/coverage_diagnostics/coverage_reason_frequency.csv && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/W2a_large_n3000_seed42/coverage_diagnostics/empty_state_decomposition.json && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42/coverage_diagnostics/coverage_diagnostic_summary.json && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42/coverage_diagnostics/coverage_diagnostic_customer_breakdown.csv && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42/coverage_diagnostics/coverage_reason_frequency.csv && test -f artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42/coverage_diagnostics/empty_state_decomposition.json` | ❌ W0 | ⬜ pending |
| 71-02-03 | 02 | 2 | COV-02,COV-03 | report-check | `test -f .planning/phases/71-coverage-diagnostics-failure-analysis/71-02-SUMMARY.md && rg -n \"Phase 72 recommendation\" .planning/phases/71-coverage-diagnostics-failure-analysis/71-02-SUMMARY.md >/dev/null` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers Phase 71 needs:
- `credit-coach/tests/test_cohort_evaluation.py` — cohort runner stability checks

Wave 1 introduces new unit tests:
- `credit-coach/tests/test_coverage_diagnostics.py`

---

## Manual-Only Verifications

If Phase 71 is integrated into the cohort runner by default, do one quick manual scan after Wave 1:
- ensure no changes to existing `cohort_metrics.json` keys and report text (additive file emission only)

---

## Validation Sign-Off

- [ ] All tasks have automated verify or bounded manual checks
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all dependencies
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter when complete

**Approval:** pending
