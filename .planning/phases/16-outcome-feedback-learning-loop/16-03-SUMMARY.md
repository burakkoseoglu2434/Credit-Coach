---
phase: 16-outcome-feedback-learning-loop
plan: 03
subsystem: off-policy-evaluation
tags: [ope, ips, doubly-robust, control-baseline, review, pytest]
requires: [16-01, 16-02]
provides:
  - canonical IPS and Doubly Robust helpers over the locked proxy vector
  - confidence-aware OPE artifacts with graceful degradation
  - preferred-policy and metric-label reporting under `Learning Loop Summary`
affects: [phase-16, evaluation, outcome-feedback, suite, review]
tech-stack:
  added: [credit-coach/src/credit_coach/evaluation/off_policy.py]
  patterns: [proxy-vector-first OPE, control baseline, confidence-aware degradation]
key-files:
  created: [credit-coach/src/credit_coach/evaluation/off_policy.py, credit-coach/tests/test_off_policy_evaluation.py]
  modified: [credit-coach/src/credit_coach/cli/run_outcome_feedback.py, credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py, credit-coach/src/credit_coach/ops/kpi_contract.py, credit-coach/tests/test_outcome_feedback.py, credit-coach/tests/test_phase_experiment_suite.py, credit-coach/tests/test_kpi_contract.py]
key-decisions:
  - "OPE stays proxy-vector-first over `approval_rate`, `default_rate_90d`, and `avg_margin_90d`."
  - "`control` remains the canonical comparative baseline; missing control degrades to tentative descriptive evidence."
  - "OPE remains mandatory supporting evidence, non-blocking, and confidence-aware."
patterns-established:
  - "Learning review now exposes policy signals as metric labels such as `supports_treatment`, `supports_control`, `mixed`, or `insufficient_evidence`."
requirements-completed: [REC-11]
duration: manual-execution
completed: 2026-03-16
---

# Phase 16 Plan 03 Summary

**The repo can now evaluate logged policy behavior with explicit IPS and Doubly Robust evidence instead of heuristic-only comparisons.**

## Accomplishments
- Added `evaluation/off_policy.py` for canonical IPS and Doubly Robust estimation over approval, default, and margin proxy rewards.
- Implemented confidence downgrades for weak propensities, low reward coverage, arm imbalance, and missing control baselines.
- Surfaced preferred policy signals and metric-by-metric OPE labels inside the new `Learning Loop Summary` without redefining milestone acceptance or release gating.

## Verification
- `python -m pytest credit-coach/tests/test_off_policy_evaluation.py credit-coach/tests/test_outcome_feedback.py credit-coach/tests/test_phase_experiment_suite.py credit-coach/tests/test_kpi_contract.py`

## Notes
- OPE is evidence-first and non-blocking by design.
- Control-baselined comparisons remain the only source for strong comparative policy claims in this phase.

---
*Phase: 16-outcome-feedback-learning-loop*
*Completed: 2026-03-16*
