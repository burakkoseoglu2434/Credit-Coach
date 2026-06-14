---
phase: 72-recoverability-gate-relaxation-controlled
plan: 02
subsystem: evaluation
tags: [recoverability, recourse, gating, assisted_full, thresholds, w2a, report]

provides:
  - deterministic assisted_full threshold scanner + locked config writer
  - baseline vs intervention evaluation runs (n=500, seed=42)
  - Phase 72 report with rollback statement and Phase 73 go/no-go

key-files:
  created:
    - .planning/phases/72-recoverability-gate-relaxation-controlled/72-REPORT.md
  modified:
    - credit-coach/src/credit_coach/cli/run_v27_assisted_full_threshold_scan.py
    - credit-coach/configs/recourse_assisted_full_w2a_locked.yaml

duration: 0m
completed: 2026-04-20
---

# Phase 72 Plan 02: Threshold Lock + Baseline vs Intervention Report — Summary

## What this did

- Added a deterministic CLI to scan a baseline `customer_level_analysis.csv`, choose assisted_full thresholds to target ~7–12% eligibility share, and write a locked recourse config YAML.
- Ran a baseline (assisted_full disabled) vs intervention (assisted_full enabled + locked thresholds) cohort evaluation and published a Phase 72 report with a strict rollback statement.

## Key results (global denied; n=500, seed=42)

- Trust counters (rollback gates): `invalid_winner=0`, `surface_drift=0`, `operator_contradiction=0` (baseline and intervention)
- Empty-state rate: `98.4%` → `93.2%` (**-5.2 pp**)
- Actionable share: `1.6%` → `6.8%` (**+5.2 pp**, ~`4.25×`)
- Assisted_full share (recourse_mode): `0.0%` → `5.2%`

## Locked thresholds

From `credit-coach/artifacts/evaluations/v27_assisted_full_thresholds_W2a.json`:
- `threshold_prob_min = 0.98`
- `gap_closure_rate_min = 0.20`
- `gap_divide_epsilon = 1e-06`

## Artifacts

- Baseline run: `credit-coach/artifacts/evaluations/v27_w2a_control_eval_20260420_full_processed_n500_seed42/`
- Intervention run: `credit-coach/artifacts/evaluations/v27_w2a_assisted_full_eval_20260420_full_processed_n500_seed42/`
- Locked thresholds JSON: `credit-coach/artifacts/evaluations/v27_assisted_full_thresholds_W2a.json`
- Locked recourse config: `credit-coach/configs/recourse_assisted_full_w2a_locked.yaml`
- Report: `.planning/phases/72-recoverability-gate-relaxation-controlled/72-REPORT.md`

## Commits

- `7b4a5e0` feat(72-02): add assisted_full threshold scanner CLI
- `74785e2` fix(72-02): target global share in threshold scan
- `a6a5ba5` fix(72-02): write assisted_full config under recourse_gate
- `8285e2b` feat(72-02): lock assisted_full thresholds for W2a
- `7fba48b` fix(72-02): include assisted_full in recourse metrics

## Deviations from Plan

- Ran W2a baseline/intervention at `n_customers=500` (seed `42`) for iteration speed; re-run with `n_customers=3000` for final milestone-grade numbers.

## Self-Check: PASSED

- Baseline + intervention run dirs exist with `cohort_metrics.json` and `customer_level_analysis.csv`
- Intervention trust counters are all zero
- Phase 72 report includes explicit rollback statement and Phase 73 go/no-go

