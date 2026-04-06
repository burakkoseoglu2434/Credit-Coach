# Phase 62: Recoverable Customer Classifier - Research

**Researched:** 2026-04-06
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that turns the shipped Phase 61 recoverability signal into a deterministic runtime classifier without changing recourse routing, planner behavior, or trust-critical selected surfaces?

## Planning Basis

Phase 62 decisions were discussed in-session and are now locked in [62-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/62-recoverable-customer-classifier/62-CONTEXT.md). The authoritative inputs for this planning pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [62-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/62-recoverable-customer-classifier/62-CONTEXT.md)
- [recoverability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/recoverability.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py)
- [cohort_evidence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/cohort_evidence.py)
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
- [test_recoverability_signals.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recoverability_signals.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_cohort_evaluation.py)
- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py)
- [test_decision_ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_ownership.py)
- [test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py)
- [test_operator_packet_coherence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_packet_coherence.py)

## Executive Summary

Phase 62 should be planned as a **strict classifier overlay phase**, not as a routing or narrative phase. The cleanest implementation shape is:

`extend the shared recoverability helper with one classifier rule -> emit additive classifier fields through existing artifact seams -> prove the rule and trust preservation with focused tests`

The current repo shape strongly supports this approach:

1. the full upstream signal contract already exists in one helper
2. runtime, collection, and cohort-evaluation propagation already serialize the signal
3. no customer/operator wording needs to change yet
4. the trust suites already cover the surfaces most at risk from accidental drift

Planning implication:
- Phase 62 should piggyback on Phase 61’s shared helper and propagation seams.
- The phase should stop at additive classifier truth.
- Selected recommendation text, operator packet wording, and recourse behavior must stay unchanged.

## Concrete Repo Findings

### 1. Phase 61 already centralized the upstream signal contract

[recoverability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/recoverability.py) already owns:

- `approval_gap`
- `normalized_gap`
- `risk_band`
- `recoverability_bucket`
- `recoverability_score`
- `threshold_reach_possible`
- hard and soft blocker separation
- signal-form `recoverable_reason_codes`

Planning implication:
- Phase 62 should add classifier logic here or immediately adjacent to it.
- Recomputing classifier inputs elsewhere would create semantic drift and duplicate the Phase 61 contract.

### 2. Runtime propagation seams are already prepared

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) already:

- computes and attaches the recoverability signal into `roadmap["summary"]`
- syncs the same fields into `metrics_summary`
- exposes the summary fields through `_sync_metrics_summary_with_roadmap_summary(...)`

Planning implication:
- Phase 62 does not need a new runtime seam.
- The classifier should be computed once from the shared helper and written into `roadmap["summary"]`, then allowed to flow through the existing sync path.

### 3. Collection and evaluation propagation are already additive

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already preserves:

- recoverability bucket
- score
- threshold reachability
- blocker flags
- `recoverable_reason_codes_json`

[run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py) already writes:

- customer-level recoverability fields
- overall threshold-reach rates
- recoverability-bucket distributions

Planning implication:
- Phase 62 can extend both flows additively with:
  - `recoverable_flag`
  - classifier-form `recoverable_reason_codes`
  - classifier version
- There is no need to create a second classifier-reporting pipeline.

### 4. No downstream surface currently consumes recoverability as product truth

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py), [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py), and [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py) still derive customer/operator wording from:

- selected recommendation projection
- decision ownership outputs
- existing selected-surface logic

Planning implication:
- Phase 62 should explicitly avoid touching these files unless a trust-safe additive field is already wired through without wording changes.
- Narrative and mode changes belong to later phases.

### 5. Calibration work frames are an optional but useful analysis seam

[decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already carries additive Phase 61 fields in `build_selection_work_frame(...)`.

Planning implication:
- Phase 62 may add classifier truth here for analysis reuse.
- This should remain non-routing and non-promotional.

### 6. The new classifier vocabulary does not exist yet

Repo scan found no current usage of:

- `recoverable_flag`
- `recoverability_classifier_version`
- `WITHIN_RECOVERABLE_BAND`
- `OUTSIDE_RECOVERABLE_BAND`
- `NO_ACTIVE_CLASSIFIER_BLOCKERS`

Planning implication:
- Phase 62 needs focused unit coverage around new classifier semantics.
- This is a clean addition rather than a risky migration of existing classifier code.

## What Phase 62 Must Deliver

### 1. One canonical classifier helper on top of the signal layer

Phase 62 should add one reusable classifier derivation that owns:

- `recoverable_flag`
- classifier-form `recoverable_reason_codes`
- `recoverability_classifier_version`

The helper should:
- consume Phase 61 signal outputs
- remain deterministic
- enforce the strict near-threshold-only rule
- keep `recoverability_score` outside the decision rule

### 2. Runtime and artifact propagation without behavior change

Phase 62 should thread the classifier fields into:

- recourse roadmap summary
- recourse metrics summary
- customer artifact collection rows
- cohort-evaluation customer rows and aggregate outputs
- cohort evidence packaging

It should not:
- change selected recommendation text
- change operator packet wording
- change explanation pack wording
- change planner ranking or recourse routing

### 3. Focused proof of conservative classification behavior

The test surface should prove:

- near-threshold + rankable + threshold-reachable + blocker-free becomes recoverable
- mid-risk remains not recoverable even when threshold-reachable
- soft blockers fail classification without being mislabeled as structural limitation
- hard blockers fail classification deterministically
- runtime and audit artifacts carry classifier truth without breaking selected-surface or operator tests

## Recommended Plan Shape

The cleanest split is:

1. `62-01` - canonical classifier helper and focused classifier tests
2. `62-02` - runtime, collection, and calibration propagation of classifier fields
3. `62-03` - cohort evaluation and evidence visibility for classifier truth

## Validation Architecture

Validation should prove both classifier correctness and unchanged trust behavior:

1. Classifier rule correctness
- near-threshold-only positive gate
- threshold reachability required
- rankable path required
- hard and soft blockers both fail classification in Phase 62
- `recoverability_score` does not affect the decision

2. Runtime and artifact propagation
- runtime summaries emit the classifier fields
- collection rows preserve classifier truth without reinterpretation
- cohort evaluation writes recoverable rates and classifier distributions additively

3. Trust and surface non-regression
- selected-surface consistency remains unchanged
- operator packet coherence remains unchanged
- decision ownership remains untouched

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py tests/test_decision_calibration.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py tests/test_decision_calibration.py tests/test_decision_ownership.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py -q`

## RESEARCH COMPLETE
