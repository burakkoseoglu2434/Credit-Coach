# Phase 72: Recoverability Gate Relaxation (Controlled) — Research

**Researched:** 2026-04-18  
**Purpose:** capture the minimum operational + codebase knowledge needed to introduce an intermediate `assisted_full` tier that surfaces **existing** latent value safely, with deterministic provenance and W2a-comparable evaluation.

## Where Phase 72 must land in the shipped pipeline

The current shipped gate is binary:
- `credit-coach/src/credit_coach/evaluation/recoverability.py` → `build_recourse_gate(...)` returns:
  - `recourse_mode: full|limited`
  - `recommendation_mode: actionable|informational`
  - reason codes: `RECOVERABLE_FULL_MODE` or `NOT_RECOVERABLE_LIMITED_MODE`

Limited mode behavior is intentionally fail-closed:
- `credit-coach/src/credit_coach/cli/run_recourse.py` → `_apply_recourse_gate_to_roadmap(...)` rewrites selected truth to empty-state when `recourse_mode == limited` (clears selected-path movement fields, empties `narrative.steps`, forces selected projection empty-state).

Phase 72 must introduce a third routing tier:
- `recourse_mode: assisted_full`
- treated as **non-limited** for projection (do not apply empty-state rewrite)
- but with stricter surfacing constraints than full mode (exactly 1 minimal customer-only action, allowlisted)

## Data reality: what is and isn’t observable in W2a today

In limited mode, the system overwrites selected fields (by design). This means baseline artifacts can hide pre-gate values that are needed for calibration (e.g., `threshold_reach_probability` for the best latent plan).

However, Phase 72 can preserve calibration truth without changing selection semantics by emitting additive **pre-gate shadow fields**:
- copy the best-plan `threshold_reach_probability` and `movement_score` into `pre_gate_*` fields before limited-mode rewrites them to 0
- optionally persist the pre-gate `best_plan_id` (audit-only) for joinability/debug
- compute and persist a deterministic `gap_closure_rate` proxy using existing pre-gate values (see below)

This keeps W2a comparability intact while enabling “data-driven then locked” threshold selection.

## Eligibility signals (Wave 1, deterministic)

Phase 72 discussion decisions:
- eligibility uses OR between a threshold-proxy and a gap-closure proxy
- thresholds are chosen via W2a scan to target ~`7–12%` assisted_full share, then locked
- restrict to policy-suppressed customers (those that would otherwise be `limited`)

Recommended signals:
- `pre_gate_threshold_reach_probability` (copied from the selected/best plan before limited-mode rewrite)
- `gap_closure_rate` (explicitly computed):
  - `gap_closure_rate = best_possible_pd_improvement / max(approval_gap, epsilon)`
  - store `best_possible_pd_improvement` (currently computed but not emitted)
  - use an explicit epsilon to avoid divide-by-zero

Additional Wave 1 constraints from the phase context:
- customer-only only (`selected_path_type == customer_only`)
- no institution-assisted actions (must reject steps requiring institutional approval)
- allowlisted minimal action key(s) only

## Minimal action surfacing (Wave 1)

The recourse roadmap phases contain step-level action metadata:
- Narrative generation (`credit-coach/src/credit_coach/coaching/messaging.py:build_customer_roadmap_narrative`) iterates `phases[*].steps[*]` and reads `action_key`, plus offer contract fields like `requires_institutional_approval`.

Therefore, minimal surfacing can be implemented as a deterministic **roadmap/narrative pruner** for assisted_full:
- choose exactly one step whose `action_key` is allowlisted
- require `requires_institutional_approval == false` and `requires_acceptance == false`
- prune roadmap phases and narrative steps to that single action
- ensure that if no allowlisted step exists, the customer falls back to `limited` (no forced actions)

Wave 1 allowlist (from discussion):
- `adjust_requested_loan_amount`
- plus one utilization action: `limit_credit_usage` and/or `reduce_spending` (deterministic preference order)

## Provenance requirements (GATE-03)

Keep existing reason codes stable (do not rename), but add explicit provenance for assisted_full:
- `assisted_full_reason_codes` (deterministic string taxonomy)
- `assisted_full_thresholds` (the locked numeric threshold values and epsilons)

Also preserve auditability:
- store pre-gate values under `pre_gate_*` fields so Phase 72 evaluation can explain why a customer changed tiers.

## Evaluation protocol

Mandatory baseline comparison:
- W2a baseline (assisted_full disabled)
- W2a intervention (assisted_full enabled with locked thresholds)

Metrics to publish (overall + by segment):
- actionable coverage uplift and empty-state reduction
- trust counters (must remain zero)
- action-type distribution changes (even though only 1 action is surfaced, distribution should become less dominated by a single family over time; Wave 1 is expected to be conservative)
- segment-level uplift (`near_threshold`, `mid_risk`, `hard_denied`)

Rollback condition:
- any non-zero trust counter aborts (`selected_invalid_winner_count`, `selected_surface_drift_count`, `operator_packet_contradiction_count`)

## Validation Architecture

Phase 72 uses a “trust-first” validation contract:
- Unit tests lock assisted_full routing, allowlist pruning, and fallback behavior.
- Regression tests keep cohort evaluation contract stable.
- Intervention runs must hard-assert trust counters remain zero.

Source of truth: `.planning/phases/72-recoverability-gate-relaxation-controlled/72-VALIDATION.md`

## Implementation seams (recommended)

1) Gate tier selection:
- implement in `credit-coach/src/credit_coach/cli/run_recourse.py:_apply_recourse_gate_to_roadmap(...)` where the gate result is applied and limited rewrite happens.
- optionally extend `credit-coach/src/credit_coach/evaluation/recoverability.py:build_recourse_gate(...)` to support `assisted_full` if you prefer centralization, but the assisted_full surfacing constraint will still be enforced in `run_recourse.py`.

2) Additive calibration truth:
- persist `pre_gate_*` and `best_possible_pd_improvement` / `gap_closure_rate` into roadmap summary before any limited-mode rewrites.

3) Configuration toggle:
- add a config section (e.g., in `credit-coach/configs/recourse.yaml`) controlling:
  - `assisted_full.enabled`
  - `threshold_reach_probability_min`
  - `gap_closure_rate_min`
  - `gap_divide_epsilon`
  - `allowlisted_action_keys` and preference order

## Risks and pitfalls

- Assisted_full must not accidentally include hybrid/institution paths in Wave 1 (enforce `selected_path_type == customer_only` and enforce step-level institutional flags).
- If a customer is eligible by signal but has no allowlisted action step, forced surfacing risks noise and contradictions — must fall back to limited.
- Ensure operator packet coherence remains clean; any contradiction should be treated as rollback.

---

## RESEARCH COMPLETE
