# Phase 61: Recoverability Signal Definition - Research

**Researched:** 2026-04-05
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that adds a deterministic recoverability signal layer over the shipped v2.4 runtime without changing planner behavior, decision thresholds, or recourse routing?

## Planning Basis

Phase 61 decisions were discussed in-session and are now locked in [61-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/61-recoverability-signal-definition/61-CONTEXT.md). The authoritative inputs for this planning pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [61-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/61-recoverability-signal-definition/61-CONTEXT.md)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py)
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
- [cohort_evidence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/cohort_evidence.py)
- [recourse.yaml](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/configs/recourse.yaml)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_cohort_evaluation.py)
- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py)
- [test_decision_ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_ownership.py)

## Executive Summary

Phase 61 should be planned as a **shared signal derivation phase**, not as a decision or routing phase. The safest implementation shape is:

`derive one canonical recoverability helper -> thread additive signal fields into existing runtime and evaluation outputs -> prove the signal with focused deterministic tests`

The repo scan shows that most of the raw ingredients already exist:

1. raw threshold distance already exists as `base_pd - tau`
2. absolute denied-distance thresholds are already locked in config and runtime helpers
3. existing recourse outputs already expose enough path and blocker information to derive threshold reachability and structural flags
4. collection and cohort evaluation flows already serialize the right customer-level and cohort-level seams for additive signal fields

That means Phase 61 should avoid inventing a second theory of recoverability. It should package the current distance, path, and blocker signals into one reusable helper and then expose those signals consistently in runtime and audit artifacts.

## Concrete Repo Findings

### 1. Raw threshold distance is already a shipped concept

[run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py) already computes:

- `approval_gap = max(0, base_pd - tau)`

[decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already builds:

- `pd_distance_to_tau`
- `pilot_bucket`
- `risk_band`

Planning implication:
- Phase 61 should standardize on raw threshold distance as the canonical recoverability input.
- It should not introduce percentile-based or feature-gap alternatives.

### 2. The bucket thresholds are already stable and absolute

[recourse.yaml](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/configs/recourse.yaml) and [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) already lock:

- `near_upper = 0.10`
- `mid_upper = 0.25`

The runtime helper `_risk_band_from_pd(...)` already maps raw gap to `near`, `mid`, and `high`.

Planning implication:
- Phase 61 should reuse these thresholds directly.
- `recoverability_bucket` should be a thin business-facing layer over the existing `risk_band` semantics rather than a new segmentation regime.

### 3. Threshold reachability can be derived from shipped path outputs

[run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py) already computes:

- `max_path_pd_improvement`
- `best_reachable_pd`
- `path_reaches_threshold_flag`
- gap-closure rate heuristics

Planning implication:
- Phase 61 does not need to simulate new plans to estimate threshold reachability.
- A deterministic `threshold_reach_possible` field can be derived from existing rankable-path outputs using the locked heuristic from context.

### 4. Structural blockers already exist in repo vocabulary

[decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already distinguishes:

- recommendation-space blocker signals such as `NO_PATH` and `LOW_IMPACT`
- structural cohort signals such as `TIME_BLOCK`, `OFFER_BLOCK`, `NO_VALID_WINNER`, and high-risk concentration

[decision/ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) already exposes:

- `rejection_type`
- `conditional_type`
- `expected_readiness`
- `decision_reason_primary`

Planning implication:
- Phase 61 should derive recoverability reason codes from this existing blocker language.
- Hard-vs-soft structural blocker categorization can be additive without changing the current decision semantics.
- `LOW_EXECUTION` and `DATA_ISSUE` should remain in the existing decision-owner explanation layer unless they map cleanly onto already-locked Phase 61 recoverability codes. Phase 61 should not create extra blocker families for them.

### 5. Runtime artifact seams already exist for additive signal fields

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) already builds:

- `roadmap["summary"]`
- `metrics_summary`

These are the two main customer-level seams consumed later by collection, calibration, and evaluation.

Planning implication:
- Phase 61 should compute recoverability signals once and write them into both runtime summaries.
- That keeps the signal reusable for later phases without re-deriving it in every consumer.
- For non-denied or mixed-cohort rows, the minimal safe contract is:
  - always compute `approval_gap`, `normalized_gap`, and bucket semantics from `base_pd` and `tau`
  - only emit denied-specific structural interpretation fields when the current row actually has denied-mode semantics

### 6. Collection and cohort evaluation already expose audit-friendly outputs

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already assembles one customer-level metrics row from selection metadata, roadmap summary, and path metrics.

[run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py) already writes:

- customer-level CSV
- summary JSON
- Markdown report

Planning implication:
- Phase 61 should use these as the required audit surfaces for `RECV-04`.
- It does not need a new reporting pipeline.

## What Phase 61 Must Deliver

### 1. One canonical recoverability helper

Phase 61 should add one shared helper module that owns:

- `approval_gap`
- `normalized_gap`
- `risk_band`
- `recoverability_bucket`
- `recoverability_score`
- `threshold_reach_possible`
- helper flags such as valid-path and structural-blocker indicators
- compositional reason-code derivation

### 2. Runtime integration without behavioral drift

Phase 61 should thread the shared signal into:

- recourse roadmap summary
- recourse metrics summary
- collection metrics rows
- selection/evaluation work frames where additive signal fields improve downstream reuse

No planner ranking, no winner logic, and no routing changes belong here.

### 3. Evaluation visibility for auditability

Phase 61 should extend the existing cohort evaluation outputs so the recoverability signal fields are visible in customer-level artifacts and easy to inspect in aggregate summaries.

### 4. Focused deterministic test proof

The test surface should prove:

- raw gap and normalization math
- absolute bucket boundaries
- gap-only score behavior
- threshold-reach heuristic
- hard-vs-soft blocker classification
- artifact propagation into collection and cohort outputs

## Recommended Plan Shape

The cleanest split is:

1. `61-01` - shared recoverability helper and focused signal tests
2. `61-02` - runtime and collection integration for additive recoverability fields
3. `61-03` - cohort-evaluation/export integration and audit-surface tests

## Validation Architecture

Validation should prove both signal correctness and unchanged runtime semantics:

1. Core signal correctness
- raw gap math uses `base_pd - tau`
- score stays `1.0 - normalized_gap`
- bucket boundaries remain absolute at `0.10` and `0.25`
- threshold reachability uses existing path outputs only

2. Runtime integration integrity
- recourse summaries and collection metrics expose the same recoverability fields
- collection rows do not silently reinterpret or recompute the signal
- existing trust-critical fields remain untouched

3. Evaluation visibility
- customer-level cohort analysis outputs include the new signal fields
- aggregate summaries can report recoverability distributions without hiding the raw customer-level seam

4. Scope discipline for mixed rows and unrelated blockers
- `DATA_ISSUE` must remain a decision/trust explanation, not a recoverability blocker family
- `LOW_EXECUTION` should not become a new Phase 61 structural category unless it is already represented by locked blocker semantics
- mixed or non-denied rows should not force a fake denied-only structural interpretation

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py tests/test_decision_calibration.py tests/test_decision_ownership.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py -q`

## RESEARCH COMPLETE
