# Phase 48: Operator Packet Coherence - Research

**Researched:** 2026-04-01
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that makes operator packets internally coherent across blockers, next actions, readiness, and decision state without reopening selected truth, winner integrity, or decision semantics?

## Planning Basis

Phase 48 decisions were discussed in-session and are now locked in [48-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/48-operator-packet-coherence/48-CONTEXT.md). For this planning pass the authoritative inputs are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [45-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/45-winner-integrity-hard-stop/45-CONTEXT.md)
- [46-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/46-dice-lane-validity-enforcement/46-CONTEXT.md)
- [47-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/47-selected-surface-consistency/47-CONTEXT.md)
- [48-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/48-operator-packet-coherence/48-CONTEXT.md)
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py)
- [messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py)
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py)
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [test_operator_review_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_review_pack.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_phase_experiment_suite.py)

This is sufficient because earlier phases already fixed the upstream trust chain:

- Phase 45 hard-stopped invalid selected winners
- Phase 46 ensured selected DICE winners are contender-clean
- Phase 47 aligned selected projection ownership across raw, flat, operator, and explanation surfaces

The remaining gap is not selected truth anymore. It is **operator packet render coherence**.

## Executive Summary

Phase 48 should be planned as a **status-aware packet rendering and proof phase**, not as a selected-truth phase and not as a decision-threshold phase.

The safest shape is:

`status-aware packet render contract -> packet coherence diagnostics -> flat/summary propagation -> rerun proof`

The code scan shows five important truths:

1. [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) already owns short-view blockers, actions, readiness notes, markdown rendering, and packet metrics, so Phase 48 should stay concentrated there rather than diffusing logic across surfaces
2. `_fallback_blocker(...)` in [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) is the main incoherence seam because it currently fabricates blockers even when the packet decision state should suppress them
3. [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) already owns decision status, readiness, reason drivers, and upgrade condition, so Phase 48 should interpret those fields differently by packet state rather than redefining them
4. [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py) already provides `OperatorPacketShortView` and `OperatorPacketTechnicalAppendix`, so additive render-source and coherence-diagnostic fields fit naturally without creating a new artifact family
5. [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already lifts operator packet fields into flat metrics and collection summaries, so Phase 48 acceptance can be proven in the same rerun evidence system as Phases 45-47

## Concrete Repo Findings

### 1. Approved packets still inherit fallback blockers

[operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) currently does:

- if `decision_reason_drivers` are empty, `_blockers_from_summary(...)` falls back to `_fallback_blocker(...)`
- `_fallback_blocker(...)` keys off `decision_reason_primary`

That is safe for some `CONDITIONAL` and `REJECTED` packets, but it is not safe for `APPROVED`. This is the cleanest Phase 48 bug seam.

### 2. Actions are projection-owned, but not yet status-aware

[operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) now consumes the Phase 47 selected projection, which is good. But it still assumes that if a selected projection exists, it should render as a short-view action.

Phase 48 should keep selected projection ownership intact while making action rendering **packet-mode aware**:

- suppress for `APPROVED`
- suppress for `empty_state`
- keep for `CONDITIONAL`
- allow only controlled use for `REJECTED`

### 3. Readiness notes are not yet render-mode aware

[messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py) already has a generic `build_operator_readiness_note(...)`. Phase 48 does not need new readiness semantics, but packet rendering does need a stricter interpretation layer:

- readiness as information for `APPROVED`
- readiness as time or manual-review context for `CONDITIONAL`
- readiness as non-upgrade language for `REJECTED`
- readiness as context-only for `no_valid_winner`

### 4. Packet appendix is the right place for coherence diagnostics

[schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py) already gives `OperatorPacketTechnicalAppendix` enough room to carry additive fields like render source, suppression flags, and coherence codes. This means Phase 48 can expose why the packet rendered a certain way without polluting short-view business semantics.

### 5. Collection proof can reuse the existing rerun pipeline

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already exports operator packet metrics. That means Phase 48 can be proven with:

- packet-level unit tests
- flat-metric counters
- three deterministic 250-customer reruns

without inventing a new evaluation toolchain.

## What Phase 48 Must Deliver

### 1. Status-aware packet rendering

The packet must assemble blockers, actions, readiness, and upgrade path differently for:

- `APPROVED`
- `CONDITIONAL`
- `REJECTED`
- `no_valid_winner`

### 2. Fallback suppression instead of fallback invention

When the packet would otherwise fabricate an incoherent blocker or action, the correct behavior is suppression plus diagnostics, not freeform filler text.

### 3. First-class coherence diagnostics

Phase 48 should emit packet render provenance such as:

- blocker render source
- action render source
- readiness render mode
- fallback suppression flag
- packet coherence codes

### 4. Rerun-readable coherence proof

Collection outputs must be able to answer:

- how many approved packets still have blockers?
- how many empty-state packets still show actions?
- how many packets have action/blocker mismatch?
- how many packets use suppressed fallback instead of incoherent filler?

## Validation Architecture

Phase 48 needs one dedicated operator-coherence test seam plus extensions to operator packet, collection, and rerun compatibility tests:

- a new `test_operator_packet_coherence.py`
- targeted operator packet tests for each decision-state mode
- collection tests for packet coherence metrics and counters
- rerun proof on `pilot_mixed`, `risk_band_balanced`, and `offer_needed_balanced`

## Recommended Plan Shape

The cleanest split is:

1. `48-01` — status-aware blocker/action/readiness contract in `operator_review.py`
2. `48-02` — schema, flat metric, and collection summary propagation for packet coherence diagnostics
3. `48-03` — regression closure plus three-cohort rerun proof using operator packet coherence counters
