# Phase 65: Targeted Cohort Evaluation - Research

**Researched:** 2026-04-10
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest deterministic evaluation extension that can prove whether `v2.5` recoverability targeting plus movement-focused ranking concentrates useful movement and improves honesty relative to the global denied baseline, without changing live runtime behavior?

## Planning Basis

Phase 65 decisions were discussed in-session and are now locked in [65-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/65-targeted-cohort-evaluation/65-CONTEXT.md). The authoritative inputs for this planning pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [61-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/61-recoverability-signal-definition/61-CONTEXT.md)
- [62-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/62-recoverable-customer-classifier/62-CONTEXT.md)
- [63-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/63-recourse-gating-by-recoverability/63-CONTEXT.md)
- [64-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/64-movement-focused-path-ranking/64-CONTEXT.md)
- [65-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/65-targeted-cohort-evaluation/65-CONTEXT.md)
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py)
- [cohort_evidence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/cohort_evidence.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [test_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_cohort_evaluation.py)

## Executive Summary

Phase 65 should be planned as a **targeted reporting and comparison extension of the existing cohort runner**, not as a new evaluation system. The safest implementation shape is:

`label the current runtime rows with explicit targeted populations -> compute deterministic targeted-vs-global comparison metrics from already-emitted recoverability, gate, and movement truth -> publish those comparisons in the existing metrics/evidence/report artifacts -> end with a constrained conclusion that states whether movement concentration improved without claiming business uplift`

The repo is already set up for this:

1. Phase 61-64 already emit the recoverability, gating, and movement fields this phase needs.
2. `run_v24_cohort_evaluation.py` already writes customer rows, aggregate metrics, and a markdown report from runtime-first truth.
3. `cohort_evidence.py` already packages additive evidence tables, including movement-ranking outputs from Phase 64.
4. `test_cohort_evaluation.py` already exercises empty, batch, artifact-writer, and end-to-end runner behavior.

Planning implication:
- Phase 65 should stay inside the current cohort-evaluation and evidence seams.
- It should not reopen planner, selected-surface, or downstream operator/explanation semantics.
- The main new artifact value is explicit targeted-comparison reporting, not a new scoring system.

## Concrete Repo Findings

### 1. The current runner already carries the exact truth Phase 65 needs

[run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py) already places these fields into `customer_row`:

- `recoverable_flag`
- `recoverability_bucket`
- `recourse_mode`
- `recommendation_mode`
- `selected_action_count`
- `selected_recommendation_source`
- `movement_score`
- `threshold_reach_probability`
- `threshold_reach_priority_flag`
- `selected_path_movement_strength`

Planning implication:
- Phase 65 should derive comparison populations and targeted summaries from these runtime-emitted fields only.
- No second recoverability or movement interpretation layer is needed downstream.

### 2. The aggregate metrics seam is centralized and easy to extend

[_aggregate_metrics(...)](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py) already computes:

- recoverability rates and distributions
- recourse-mode and recommendation-mode distributions
- movement strength and threshold-reaching aggregates
- selected-path and path-diversity diagnostics

Planning implication:
- Phase 65 should reuse `_aggregate_metrics(...)` for population-specific slices instead of building a second aggregation pathway.
- The missing contract is not raw metrics, but **explicit targeted population comparisons and conclusion framing**.

### 3. The current comparison surface is still tertile-centric, not targeting-centric

The runner currently emphasizes:

- `near_threshold_denied`
- `mid_risk_denied`
- `hard_denied`

through:

- `_comparison_rows(...)`
- `_top_five_insights(...)`
- `_diagnosis_text(...)`
- `_render_report(...)`

Planning implication:
- Phase 65 should keep those cohort slices as secondary diagnostics, but the primary comparison layer must shift to:
  - `global_denied`
  - `recoverable_full_mode`
  - `non_recoverable_limited_mode`

### 4. Evidence packaging is additive and already movement-aware

[cohort_evidence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/cohort_evidence.py) already exposes:

- selected-path distribution
- recoverability signal
- recourse gate
- movement ranking
- trust regression

Planning implication:
- Phase 65 should extend the existing evidence package with targeted-comparison populations or tables.
- It should not invent a parallel reporting package disconnected from the current evidence writer.

### 5. The report still speaks in `v2.4` capability-evaluation language

[_render_report(...)](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py) still renders:

- `# v2.4 Cohort Evaluation`
- `Evaluation mode: existing v2.4 recourse pipeline only`
- `Does v2.4 increase movement potential?`
- `Is system ready for business uplift experiments?`

Planning implication:
- Phase 65 should update the report framing so it speaks about `v2.5` targeting concentration and honesty, not general `v2.4` capability expansion.
- This is a reporting change only, not a runtime-policy change.

### 6. The current test surface is already enough for this phase

[test_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_cohort_evaluation.py) already covers:

- empty-population metric summaries
- evidence package and writer contracts
- end-to-end runner outputs for recoverable/full and limited/empty-state cases

Planning implication:
- Phase 65 can likely be proven entirely through this existing test file.
- No separate trust-regression wave is necessary unless implementation spills outside the evaluation seam.

## What Phase 65 Must Deliver

### 1. Explicit targeted populations

Phase 65 should add deterministic population labels and population summaries for:

- `global_denied`
- `recoverable_full_mode`
- `non_recoverable_limited_mode`

Optional secondary slices remain:

- `recoverability_bucket`
- current tertile cohorts

### 2. Small decisive comparison metrics

The primary outputs should include:

- `recoverable_customer_rate`
- `movement_rate_global`
- `movement_rate_recoverable`
- `strong_movement_rate_global`
- `strong_movement_rate_recoverable`
- `mean_movement_score`
- `mean_threshold_reach_probability`
- `threshold_reach_priority_rate`
- `selected_path_movement_strength_distribution`
- `threshold_gap_distribution`
- `recommendation_mode_distribution`
- `limited_customer_rate`
- `informational_recommendation_rate`
- `empty_state_rate`

### 3. A canonical targeted-comparison artifact surface

Phase 65 should publish targeted comparisons in:

- `cohort_metrics.json`
- `cohort_evaluation_report.md`
- additive evidence table(s) if needed

The canonical human-readable answer should live in the markdown report.

### 4. Deterministic conclusion framing

The phase must end with a report statement that says whether targeting:

- improved concentration
- failed to improve concentration
- improved concentration but not enough to imply business leverage
- or remained inconclusive

This conclusion must stay strictly non-causal and non-uplift-claiming.

## Recommended Plan Shape

The cleanest split is:

1. `65-01` - add explicit targeted population labels and aggregate comparison metrics inside the current cohort runner
2. `65-02` - propagate those comparisons into evidence tables, machine-readable artifacts, and report sections
3. `65-03` - replace old `v2.4` capability framing with final `v2.5` targeting concentration and honesty conclusions

## Validation Architecture

Validation should prove metric correctness, artifact completeness, and non-hype conclusion framing:

1. Population labeling and metric aggregation
- recoverable/full-mode and non-recoverable/limited-mode rows are labeled deterministically from runtime truth
- targeted comparison metrics reflect those labels correctly

2. Artifact propagation
- `customer_level_analysis.csv`, `cohort_metrics.json`, and report/evidence outputs expose the new targeted-comparison contract
- threshold-gap and honesty-control metrics are emitted without recomputing runtime truth

3. Report conclusion discipline
- the report clearly states concentration results
- the report does not imply business uplift or causal outcome proof
- limited mode is shown as an honesty/control group rather than omitted

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q`

## RESEARCH COMPLETE
