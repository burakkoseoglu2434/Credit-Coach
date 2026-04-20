# Phase 72 Report: Recoverability Gate Relaxation (Controlled)

**Generated:** 2026-04-20  
**Scope:** Phase 72 Wave 2 — baseline vs assisted_full intervention (controlled unlock)  
**Note:** Runs below use `n_customers=500` (seed `42`) for a faster iteration loop. Re-run with `n_customers=3000` for final milestone-grade numbers.

## Runs (Artifacts)

**Baseline (control; assisted_full disabled)**
- `credit-coach/artifacts/evaluations/v27_w2a_control_eval_20260420_full_processed_n500_seed42/`

**Intervention (assisted_full enabled; locked thresholds)**
- `credit-coach/artifacts/evaluations/v27_w2a_assisted_full_eval_20260420_full_processed_n500_seed42/`

**Threshold locking (scanner output)**
- `credit-coach/artifacts/evaluations/v27_assisted_full_thresholds_W2a.json`

**Locked runtime config**
- `credit-coach/configs/recourse_assisted_full_w2a_locked.yaml`

## Locked thresholds (data-driven then frozen)

Scanner targets an assisted_full-eligibility share in the **7–12%** range (global denied), then locks numeric thresholds for reproducible comparisons.

Locked values:
- `threshold_prob_min = 0.98`
- `gap_closure_rate_min = 0.20`
- `gap_divide_epsilon = 1e-06`

## Headline results (global denied)

**Trust counters (rollback gates)**
- Baseline: `invalid_winner=0`, `surface_drift=0`, `operator_contradiction=0`
- Intervention: `invalid_winner=0`, `surface_drift=0`, `operator_contradiction=0`

**Recourse mode mix**
- Baseline: `full=1.6%`, `assisted_full=0.0%`, `limited=98.4%`
- Intervention: `full=1.6%`, `assisted_full=5.2%`, `limited=93.2%`

**Empty-state rate**
- Baseline: `98.4%`
- Intervention: `93.2%`
- **Delta:** `-5.2 pp`

**Actionable recommendation share** (via `recommendation_mode=actionable`)
- Baseline: `1.6%`
- Intervention: `6.8%`
- **Delta:** `+5.2 pp` (≈ `4.25×`)

## Eligibility vs realized assisted_full (why share shrinks)

The scanner locks thresholds on **signal eligibility**, but Wave 1 also enforces:
- customer-only path restriction, and
- allowlisted single-step surfacing with fallback-to-limited if no allowlisted step is present.

Observed on the intervention run:
- **Eligible-by-signal share (computed from thresholds):** `10.2%`
- **Realized assisted_full share (recourse_mode):** `5.2%`

Interpretation: roughly half of signal-eligible customers fall back to `limited` due to Wave 1 surfacing constraints (by design).

## Segment-level outcomes (by cohort label)

**near_threshold_denied**
- Empty-state: `95.2%` → `82.0%` (**-13.2 pp**)
- Assisted_full share: `13.17%`

**mid_risk_denied**
- Empty-state: `100.0%` → `98.8%` (**-1.2 pp**)
- Assisted_full share: `1.20%`

**hard_denied**
- Empty-state: `100.0%` → `98.8%` (**-1.2 pp**)
- Assisted_full share: `1.20%`

## Surfaced minimal action distribution (Wave 1)

Among `assisted_full` customers (`n=26` in this run), the surfaced minimal action is dominated by:
- `adjust_requested_loan_amount`: `26/26` (100%)

This is consistent with Wave 1’s conservative allowlist + deterministic preference order.

## Rollback statement (strict)

Rollback is **not triggered** for this iteration:
- `selected_invalid_winner_count = 0`
- `selected_surface_drift_count = 0`
- `operator_packet_contradiction_count = 0`

## Phase 73 readiness recommendation

**Go** for Phase 73 (Action Surface Expansion):
- Trust remains clean (all rollback counters zero).
- Coverage uplift is material (empty-state reduced by `5.2 pp`, actionable share +`5.2 pp`).

If additional uplift is desired before Phase 73:
- tune thresholds downward (still within Phase 72’s single-policy-change boundary), and/or
- revisit Wave 1 allowlist balance (to reduce single-action dominance) while keeping strict fallback semantics.

