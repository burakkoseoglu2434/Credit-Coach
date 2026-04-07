# Phase 63: Recourse Gating By Recoverability - Research

**Researched:** 2026-04-07
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that turns the shipped Phase 62 recoverable-customer classifier into deterministic recourse gating without redesigning the planner, thresholds, or trust-critical selected surfaces?

## Planning Basis

Phase 63 decisions were discussed in-session and are now locked in [63-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/63-recourse-gating-by-recoverability/63-CONTEXT.md). The authoritative inputs for this planning pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [47-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/47-selected-surface-consistency/47-CONTEXT.md)
- [48-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/48-operator-packet-coherence/48-CONTEXT.md)
- [61-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/61-recoverability-signal-definition/61-CONTEXT.md)
- [62-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/62-recoverable-customer-classifier/62-CONTEXT.md)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [recoverability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/recoverability.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py)
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
- [cohort_evidence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/cohort_evidence.py)
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py)
- [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py)
- [test_recoverability_signals.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recoverability_signals.py)
- [test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py)
- [test_winner_integrity_hard_stop.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_winner_integrity_hard_stop.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py)
- [test_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_cohort_evaluation.py)
- [test_operator_packet_coherence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_packet_coherence.py)
- [test_operator_review_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_review_pack.py)
- [test_decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_explanation_pack.py)

## Executive Summary

Phase 63 should be planned as a **thin routing-and-promotion suppression phase**, not as a planner redesign. The safest implementation shape is:

`derive one canonical recourse gate from Phase 62 classifier truth -> apply that gate before customer/operator selected truth is promoted -> propagate additive gate fields through existing artifact seams -> prove that the trusted empty-state path absorbs limited mode without drift`

The repo is already set up for this approach:

1. Phase 62 gives us one conservative classifier seam with deterministic reason codes.
2. `run_recourse.py` already centralizes selected-surface projection, metrics-summary sync, and recoverability attachment.
3. the v2.2 empty-state path is already trusted across selected surfaces, operator packets, and explanation packs.
4. collection and cohort outputs already flatten runtime summary truth into analyst-facing artifacts.

Planning implication:
- Phase 63 should reuse existing chooser and trust behavior whenever possible.
- The new work is deciding when to suppress promotion, not inventing a new recommendation state machine.
- Recoverable customers should keep the current runtime unchanged.

## Concrete Repo Findings

### 1. Phase 62 already owns the routing truth we need

[recoverability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/recoverability.py) already computes:

- `recoverable_flag`
- classifier-form `recoverable_reason_codes`
- `recoverability_classifier_version`

Planning implication:
- Phase 63 should derive `recourse_mode` directly from `recoverable_flag`.
- It should not create a second exception layer based on raw path quality, readiness, or gap size.

### 2. The runtime seam exists, but ordering matters

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) currently:

1. builds chooser and decision inputs
2. applies selected-surface projection
3. attaches recoverability signal/classifier truth
4. syncs metrics summary from roadmap summary

Planning implication:
- Phase 63 needs one explicit gate-resolution step in this flow.
- Because selected-surface projection happens before recoverability is attached today, planning must either:
  - resolve and apply the gate before selected projection, or
  - re-run or override selected-surface promotion after the gate is known.
- The safer first-wave approach is to keep chooser logic intact and apply limited-mode suppression at the promotion layer.

### 3. The existing empty-state path is exactly the contract limited mode needs

[test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py), [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py), and [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py) already encode the trusted empty-state behavior:

- `selected_recommendation_source = "empty_state"`
- no promoted recommendation text
- no promoted institution condition
- no selected actions
- explicit operator/explanation copy that no valid recommendation path is currently available

Planning implication:
- Phase 63 should route limited mode onto this existing path.
- It should not invent an `informational_only` selected-surface outcome in first wave.
- Audit distinction between organic no-valid-winner cases and gated limited-mode cases should come from the new gate fields, not from a new consumer-facing state.

### 4. Collection and cohort artifacts are already summary-first consumers

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already mirrors runtime summary truth into:

- `metrics_summary`
- `customer_metrics.csv`
- collection parity checks
- operator-packet rollups

[run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py) already resolves runtime-first truth for:

- customer-level cohort rows
- aggregate recoverability summaries
- evidence-package payloads

Planning implication:
- Phase 63 can add `recourse_mode`, `recommendation_mode`, `recourse_gate_version`, and `recourse_gate_reason_codes` additively through existing seams.
- There is no need for a new gating-reporting pipeline.

### 5. Trust regressions are already testable with the current suite

The existing suite already proves the surfaces most likely to drift:

- [test_winner_integrity_hard_stop.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_winner_integrity_hard_stop.py)
- [test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py)
- [test_operator_packet_coherence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_packet_coherence.py)
- [test_operator_review_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_review_pack.py)
- [test_decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_explanation_pack.py)

Planning implication:
- Phase 63 should prove limited mode by extending existing empty-state and coherence tests rather than introducing a new test family first.
- `GATE-03` can be verified by rerunning the current trust contract plus a few limited-mode-specific assertions.

### 6. No current schema exists for recourse gating

Repo scan found no current usage of:

- `recourse_mode`
- `recommendation_mode`
- `recourse_gate_version`
- `recourse_gate_reason_codes`

Planning implication:
- Phase 63 is a clean additive field introduction.
- It needs focused runtime and artifact tests so later phases can rely on these fields safely.

## What Phase 63 Must Deliver

### 1. One canonical gate-resolution contract

Phase 63 should add one shared gate derivation that owns:

- `recourse_mode`
- `recommendation_mode`
- `recourse_gate_version`
- `recourse_gate_reason_codes`

The rule should be:
- `recoverable_flag=true -> full/actionable`
- `recoverable_flag=false -> limited/informational`
- no exceptions in first wave

### 2. Runtime gating without chooser or planner redesign

Phase 63 should apply gating in `run_recourse.py` so that:

- `full` preserves current behavior
- `limited` suppresses promoted selected truth and reuses the empty-state surface
- raw candidate or path availability never overrides classifier routing

If limited-mode diagnostics remain available internally, they must stay non-selected and non-customer-facing.

### 3. Additive artifact propagation

The new gate fields should flow into:

- roadmap summary
- synced `metrics_summary`
- customer artifact collection rows
- calibration-ready work frames if useful for analysis
- cohort evaluation customer rows and aggregate outputs

### 4. Explicit trust proof for limited mode

The test surface should prove:

- recoverable customers still get full mode
- non-recoverable customers get limited mode with empty-state selected truth
- limited mode does not create fake actionability in operator or explanation consumers
- winner integrity and selected-surface consistency remain intact

## Recommended Plan Shape

The cleanest split is:

1. `63-01` - canonical gate resolver and runtime selected-surface suppression
2. `63-02` - collection/calibration propagation of gate fields and collection-level coherence proof
3. `63-03` - cohort/evidence reporting plus downstream trust-surface regression proof

## Validation Architecture

Validation should prove both deterministic routing and unchanged trust behavior:

1. Gate correctness
- `recoverable_flag` is the sole routing input
- `full` and `limited` are the only runtime modes
- no edge-case exception path silently bypasses the classifier

2. Runtime suppression integrity
- limited mode reuses the empty-state selected-surface path
- full mode preserves the shipped selected-path behavior
- limited mode does not leak promoted selected actions or institution conditions

3. Artifact propagation
- runtime summary, metrics summary, customer metrics, and cohort outputs carry one consistent gate contract
- collection and cohort flows do not recompute a different routing rule

4. Trust regression protection
- winner integrity still fails closed when appropriate
- selected-surface consistency still holds
- operator packet coherence and explanation-pack drift guards still hold under limited mode

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_selected_surface_consistency.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_selected_surface_consistency.py tests/test_winner_integrity_hard_stop.py tests/test_customer_artifact_collection.py tests/test_decision_calibration.py tests/test_cohort_evaluation.py tests/test_operator_packet_coherence.py tests/test_operator_review_pack.py tests/test_decision_explanation_pack.py -q`

## RESEARCH COMPLETE
