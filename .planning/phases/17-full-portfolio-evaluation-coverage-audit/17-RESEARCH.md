# Phase 17: Full Portfolio Evaluation & Coverage Audit - Research

**Researched:** 2026-03-18
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so Credit Coach can prove recommendation quality across the full evaluation population, not just curated demo cases, and publish one canonical full-cohort evidence layer that future website and proof surfaces can trust?

## Planning Basis

Phase 17 does not yet have a locked `17-CONTEXT.md`. For this planning pass, the authoritative sources are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/milestones/v1.2-ROADMAP.md`
- `.planning/milestones/v1.2-REQUIREMENTS.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONCERNS.md`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/tests/test_recourse_funnel_kpis.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach-website/server/services/demo-data.ts`

This is enough because the milestone goal is already locked at the roadmap level: Phase 17 is not new recourse logic, but a proof and validation phase over the existing `v1.2` engine. The remaining work is to turn fragmented batch and suite outputs into one canonical full-portfolio validation contract.

## Executive Summary

The repository already computes most of the ingredients needed for Phase 17:

- `run_batch_recourse_eval.py` runs the recourse engine over a population and already emits:
  - candidate-quality metrics
  - action realism metrics
  - behavior-aware metrics
  - trajectory metrics
  - offer metrics
  - row-level segment context such as `risk_band`, `income_band`, and `stress_band`
- `run_phase_experiment_suite.py` already knows how to aggregate seeded summaries and segment breakdowns
- the website already consumes curated demo and proof snapshots through `credit-coach-website/server/services/demo-data.ts`

But the current proof surface is still fragmented.

Today the repo is missing four things that Phase 17 must close:

1. **A canonical full-portfolio validation summary**
   - current summaries overemphasize denied-customer uplift and phase-specific evidence
   - there is no single artifact that answers: “Across the whole population, how many customers got plans, how many were feasible, how many were offer-bearing, how many were governance-safe, and how many improved by checkpoint?”

2. **Unified coverage semantics**
   - the engine can tell many local truths, but it cannot yet summarize:
     - plan coverage
     - feasible plan coverage
     - execution-weighted expected improvement
     - offer coverage
     - checkpoint health
     - governance-safe plan rate
   under one contract

3. **Segment-level full-cohort proof**
   - the code already carries `risk_band`, `income_band`, and `stress_band`
   - but there is no canonical segment rollup that separates:
     - total population behavior
     - denied subpopulation behavior
     - offer-bearing vs non-offer-bearing behavior
     - readiness and checkpoint performance by segment

4. **An executive review artifact that separates demo from proof**
   - the website can currently display curated stories
   - but the engine does not yet emit a review that explicitly says:
     - what is full-cohort truth
     - what is representative demo
     - where the two align
     - where curated stories are narrower than the full portfolio

The correct sequencing is:

- first define canonical full-portfolio metrics and artifact tables
- then add segment-level rollups over those metrics
- then publish an executive validation review that future website proof surfaces can consume

That sequence matches the brownfield seams already in the repo.

## Brownfield Constraints That Matter

### 1. The batch evaluator is already the population-scale seam

`credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py` is oversized and fragile, but it is still the repo’s canonical population-evaluation runner. Phase 17 should not build a parallel engine. It should extract and formalize portfolio-validation logic around this seam.

### 2. Segment context already exists and should be reused

The batch evaluator already computes or carries:

- `risk_band`
- `income_band`
- `stress_band`
- `canonical_segment_key`
- trajectory and offer-specific slice metrics

Phase 17 should reuse those fields rather than invent new segmentation vocabularies.

### 3. Suite aggregation should consume, not redefine, portfolio proof

`run_phase_experiment_suite.py` already aggregates seeded metrics. Phase 17 should let suite mirror the new portfolio validation artifacts, but the full-cohort truth should originate in the batch evaluator or a dedicated portfolio-validation helper consumed by it.

### 4. Website proof remains a downstream consumer

The website already has a demo/proof registry, but Phase 17 should stop short of changing product surfaces directly. It should produce stable engine-side artifacts that later phases can sync into website proof and demo views.

## Existing Assets We Can Reuse

### Batch output already contains most of the needed primitives

The batch evaluator already emits:

- denied uplift and approval summaries
- candidate diversity
- trajectory gate-pass rates
- offer coverage and governance-safe offer rates
- risk-band and income-band rollups

This means Phase 17 is primarily a contract and packaging problem, not a missing-computation problem.

### Phase suite already understands weighted aggregation

`run_phase_experiment_suite.py` already aggregates:

- canonical metrics across seeds
- segment breakdowns
- learning and offer metrics

That makes it the right downstream seam for mirroring Phase 17 proof artifacts later in the same phase.

### Existing tests already cover adjacent seams

Useful anchors already exist:

- `credit-coach/tests/test_recourse_funnel_kpis.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`
- `credit-coach/tests/test_phase_experiment_suite.py`

Phase 17 can add one focused test module for portfolio validation rather than inventing an entirely new test topology.

## Gaps Phase 17 Must Close

### 1. No canonical full-population artifact contract

The repo needs one machine-readable summary, likely something like:

- `portfolio_validation_summary.json`

with canonical metrics such as:

- `plan_coverage_rate`
- `feasible_plan_rate`
- `execution_weighted_expected_improvement`
- `offer_coverage_rate`
- `offer_acceptance_mean`
- `trajectory_gate_pass_rate_4w`
- `trajectory_gate_pass_rate_12w`
- `trajectory_gate_pass_rate_24w`
- `governance_safe_plan_rate`
- `learning_ready_coverage` when available

The precise names can be refined during execution, but the contract must be one-source-of-truth and full-cohort-first.

### 2. Denied-only metrics are too easy to overread

Current outputs are strong for denied-customer recourse benchmarking, but a product proof surface also needs:

- total-population coverage
- denied-population coverage
- recovery-ready denied coverage

These should be explicit rather than blended into one uplift story.

### 3. Segment proof is fragmented

Phase 17 needs canonical segment tables for:

- risk band
- income band
- stress band
- canonical multi-segment keys where useful
- checkpoint health by segment
- offer reach and governance-safe rate by segment

### 4. Proof vs demo is not yet formally separated

The system needs an executive artifact, likely:

- `portfolio_validation_review.md`

that explains:

- full-cohort findings
- strongest and weakest segments
- where demo stories are representative
- where demo stories are only illustrative

That narrative is critical before website proof/productization phases.

## Recommended Architecture

### A. Add a dedicated portfolio-validation summarizer module

The safest path is to extract full-cohort summarization into a focused helper module, likely under:

- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`

That module should:

- consume row-level batch outputs
- compute canonical portfolio metrics
- build segment rollups
- emit review-ready aggregate fields

This keeps `run_batch_recourse_eval.py` from growing even further without creating a second orchestration stack.

### B. Emit one canonical summary plus a small companion table set

Phase 17 should likely standardize around:

- `portfolio_validation_summary.json`
- `portfolio_coverage_breakdown.csv`
- `portfolio_segment_breakdown.csv`
- `portfolio_checkpoint_health.csv`
- `portfolio_offer_breakdown.csv`

The exact filenames can be tuned, but the principle should hold:

- one summary JSON
- a small, stable family of supporting CSV breakdowns

### C. Mirror the summary into seeded suite outputs only after the contract is stable

The suite should not invent its own definition of portfolio proof. It should consume the new portfolio validation outputs and produce weighted mirrors or supporting references when needed.

### D. Publish an executive review artifact before touching website proof

Phase 17 should end with a markdown review artifact that says what the full portfolio actually did. Later website phases can reframe it, but the engine should own the original truth.

## Recommended Execution Order

1. **Plan 17-01**
   - add canonical full-portfolio metrics and summary outputs
   - verify they work over the full batch population
2. **Plan 17-02**
   - add segment-level rollups and suite-aware aggregation over the same contract
3. **Plan 17-03**
   - add an executive validation review separating curated demo narratives from full-cohort proof

## Validation Implications

Phase 17 should introduce at least one dedicated test module:

- `credit-coach/tests/test_portfolio_validation.py`

and extend:

- `credit-coach/tests/test_recourse_funnel_kpis.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`
- `credit-coach/tests/test_phase_experiment_suite.py`

The validation goal is not just “artifact exists.” It is:

- full-population metrics are computed from the correct denominator
- segment rollups preserve cohort truth
- denied-only stories are explicitly separated from total-population stories
- review artifacts never overclaim beyond what the cohort data shows

## Planning Answer

Phase 17 should be planned as a **proof-contract phase**, not a new-modeling phase.

The repo already has the runner and most of the raw metrics. The missing work is to:

- package full-cohort truth canonically
- roll it up by segment
- distinguish curated demo stories from full portfolio evidence

That is the cleanest way to satisfy `PORT-01` and to unlock the later website/productization phases without making proof claims the engine cannot defend.
