# Phase 68-01 — Operator Packet Contradictions (Blocker Report)

**Run dir:** `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42`

## Executive Summary

The `operator_packet_contradiction_count=4` is driven by **exactly 4 customers** where the runtime is in **limited / informational mode** and therefore forces the **empty-state selected projection** (`selected_recommendation_source=empty_state`, `best_plan_id=null`), while the decision status is `APPROVED`.

In these cases:
- The operator packet correctly renders `operator_readiness_render_mode=empty_state_context` because `selected_recommendation_source=empty_state` is treated as an empty-state packet in `credit_coach.ops.operator_review`.
- The cohort evaluator flags a contradiction via **`readiness_mismatch`** because it only uses `selection_outcome == no_valid_winner` (and does not account for `selected_recommendation_source == empty_state` / limited-mode empty-state projection).

**Net assessment:** This looks like an **evaluation/reporting trust-check bug** (false positive) caused by limited-mode rules, not a planner/threshold/cohort-selection issue.

## Affected Customers (4)

All four are `recourse_mode=limited`, `recommendation_mode=informational`, `selected_recommendation_source=empty_state`, `selected_action_count=0`, and trigger **only** `readiness_mismatch=True`.

- `test_000157__eval_0252` (source: `test_000157`)
- `train_000395__eval_0262` (source: `train_000395`)
- `train_001284__eval_0276` (source: `train_001284`)
- `train_001294__eval_0277` (source: `train_001294`)

Debug artifacts were regenerated (no runtime changes) for auditability:
- `.planning/phases/68-real-cohort-evidence-run/68-01-operator-packet-contradictions/out/contradictions.json`
- Per-customer:
  - `.planning/phases/68-real-cohort-evidence-run/68-01-operator-packet-contradictions/out/<customer_id>/roadmap_summary.json`
  - `.planning/phases/68-real-cohort-evidence-run/68-01-operator-packet-contradictions/out/<customer_id>/operator_metrics.json`
  - `.planning/phases/68-real-cohort-evidence-run/68-01-operator-packet-contradictions/out/<customer_id>/operator_packet.md`

## Contradiction Type (Per Case)

**Type:** `readiness_mismatch` (and nothing else)

Observed pattern per case:
- `selection_outcome_summary = selected_valid_winner`
- `operator_selected_decision_status = APPROVED`
- `operator_readiness_render_mode = empty_state_context`
- `contradiction_flags.readiness_mismatch = True`

**Why the evaluator flags it:** in `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py`, readiness mismatch is computed as:
- if `selection_outcome != no_valid_winner` and `selected_status == APPROVED`, then readiness mode must be `approved_info`

**Why the operator packet renders `empty_state_context`:**
- `credit-coach/src/credit_coach/ops/operator_review.py:_is_empty_state_packet` treats **either**:
  - `selection_outcome == no_valid_winner`, **or**
  - `selected_recommendation_source == empty_state`
  as an empty-state packet.

## Root Cause Classification (What Layer Owns It?)

### Primary: Evaluation / Reporting Bug (Trust Check Logic)

The contradiction counter in the cohort evaluator does **not** account for the limited-mode empty-state projection.

In limited mode, the runner explicitly clears `best_plan_id` and forces the empty-state selected projection:
- `credit-coach/src/credit_coach/cli/run_recourse.py:_apply_recourse_gate_to_roadmap` (limited-mode branch)
  - `out["best_plan_id"] = None`
  - `summary["best_plan_id"] = None`
  - then `_build_selected_surface_projection(...)` sets:
    - `selected_recommendation_source = "empty_state"`
    - `selected_action_count = 0`
    - even if `selection_outcome` is not `no_valid_winner`

Given this runtime behavior, the trust check should treat `selected_recommendation_source == empty_state` as “empty-state context” for readiness-mode validation.

### Not Supported By Evidence: Rendering Drift / Packet Coherence Bug

The operator packet output is internally consistent with its own rules:
- It uses `selected_recommendation_source == empty_state` to select `empty_state_context`.
- It does not show actions/blockers in these cases (`operator_rendered_action_count=0`, `operator_rendered_blocker_count=0`).

### Secondary: Limited/Full Mode Narrative Mismatch (By Design, but Should Be Explicitly Handled)

These cases are “approved decision status” but “empty-state selected projection” because they are **limited/informational**.
That combination is expected per the limited-mode branch comment (“reuse the trusted empty-state selected projection”).

The contradiction arises because the evaluation trust logic is written as if empty-state only corresponds to `selection_outcome=no_valid_winner`.

## Severity

**High as a Phase 68 blocker** because it makes `operator_packet_contradiction_count` non-zero, which currently fails the Phase 68 trust-counter requirement.

**Low as a runtime safety concern** (based on the observed flags): it appears to be a **false positive** in the evaluator’s readiness-mode trust check, not an invalid-winner or surface-drift failure.

## Recommended Fix (Fix Now vs Tolerate)

**Recommendation: fix now.** This is reporting-layer trust logic; correcting it should not change planner/model/threshold behavior, but will remove false contradictions and allow Phase 68 evidence packaging to proceed.

**Likely fix location (primary):**
- `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py:_operator_packet_contradiction_flag`
  - Treat empty-state packets as:
    - `selection_outcome == "no_valid_winner"` **OR**
    - `roadmap_summary["selected_recommendation_source"] == "empty_state"`
  - Then validate readiness-mode accordingly.

**Likely fix location (secondary, keeps other tooling consistent):**
- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py` readiness mismatch aggregation
  - Same adjustment: include `selected_recommendation_source == "empty_state"` in the empty-state readiness-mode expectation (it already does this for the “empty_state_with_action_count” check).

**After fix:**
- Re-run Phase 68-01 cohort evaluation (same cohort, same runtime) to regenerate:
  - `cohort_metrics.json` (trust counters)
  - `cohort_evaluation_report.md` (trust baseline line)

