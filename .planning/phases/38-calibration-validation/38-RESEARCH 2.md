# Phase 38: Calibration & Validation - Research

**Researched:** 2026-03-22
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so Credit Coach can validate whether personalized numeric targets and portfolio impact distributions are realistic, stable, and not falsely optimistic without reopening the single-customer contracts hardened in Phases 30-37?

## Planning Basis

Phase 38 does not yet have a locked `38-CONTEXT.md`. For this planning pass, the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/31-numeric-target-engine/31-CONTEXT.md`
- `.planning/phases/32-feasibility-constraint-engine/32-CONTEXT.md`
- `.planning/phases/33-action-difficulty-execution-modeling/33-CONTEXT.md`
- `.planning/phases/34-offer-layer-integration/34-CONTEXT.md`
- `.planning/phases/35-narrative-generation-v2/35-CONTEXT.md`
- `.planning/phases/37-portfolio-level-numeric-impact/37-CONTEXT.md`
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
- `credit-coach/tests/test_portfolio_validation.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach/tests/test_kpi_contract.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`

This is sufficient because the user explicitly requested `--research` before a discuss pass, and Phase 38 is not intended to reopen:

- action taxonomy or grouped action identity
- numeric target generation
- feasibility repair or reject semantics
- difficulty or execution contracts
- offer contracts
- narrative generation
- product-surface rendering

Phase 38 should instead add one validation layer on top of the now-locked personalized planning stack.

## Executive Summary

Phase 31 created customer-specific numeric targets. Phase 32 hardened feasibility truth. Phase 33 added difficulty and follow-through realism. Phase 34 separated institution offers from customer action. Phase 35 translated the stack into narrative. Phase 36 rendered it in product surfaces. Phase 37 aggregated it into portfolio-level numeric impact.

The missing question is now narrower and more important:

- are the numeric asks realistic across the cohort
- do the apparent payoffs stay honest after realism and follow-through pressure
- are target ranges and impact distributions stable enough to trust
- where does the new personalized layer become narrow, optimistic, or fragile

The codebase already has most of the raw ingredients:

- portfolio validation owns the canonical portfolio-proof seam
- batch evaluation already emits target, feasibility, execution, offer, and numeric-impact ingredients
- suite packaging already mirrors portfolio validation and proof artifacts across seeds
- KPI review already knows how to tell a business-first validation story

What is still missing is one explicit calibration and validation layer that:

1. summarizes realism and optimism control for the personalized numeric stack
2. surfaces unstable target ranges and narrow or drifted impact distributions
3. keeps execution-aware truth primary instead of drifting back to paper uplift
4. packages the result into a business-safe validation review without hiding technical traceability

Phase 38 should therefore be planned as:

`calibration contract -> segment and drift validation -> business-safe review and suite alignment`

## Existing Assets We Can Reuse

### Portfolio validation already owns the right summary seam

- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - already computes:
    - coverage funnels
    - reality-gap summaries
    - numeric-impact metrics
    - execution-aware vs nominal payoff
    - segment rollups
    - portfolio review markdown
  - is the natural source of truth for a canonical calibration and validation family

### Batch evaluation already carries the row-level ingredients

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already emits:
    - primary numeric target information
    - feasibility outcomes
    - difficulty and execution probabilities
    - combined realization probability
    - offer-supported payoff splits
    - numeric-impact summary fields
  - is the right seam for row-level validation inputs and validation artifact emission

### Suite packaging already aggregates across seeds

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already mirrors:
    - portfolio validation summary
    - product confidence and proof summaries
    - seed-level aggregation
  - is the natural seam for calibration drift and stability rollups

### KPI review already provides the business-facing layer

- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already renders business-safe review summaries
  - can consume a new validation summary without becoming the source of truth itself

### Base PD model calibration already exists and should not be reopened

- model and conformal calibration artifacts already exist elsewhere in the repo
- Phase 38 should not turn into model retraining or classifier recalibration
- the goal here is recommendation calibration: realism, optimism control, range stability, and cohort honesty

## What Phase 38 Must Deliver

### 1. One canonical numeric-validation summary family

Phase 38 should add one source-of-truth validation block that can answer:

- how many numeric plans remain realism-clean after personalized targeting
- how much of the apparent payoff is likely false optimism
- how stable the requested target ranges are across the cohort
- whether the portfolio-level story is widening honestly or merely narrowing to easy slices

At minimum, the validation family should quantify:

- realistic target coverage or realism-clean share
- false-optimism exposure
- unstable target-range exposure
- distribution drift or narrowness pressure
- calibrated execution-aware payoff carry-through

### 2. Row-level validation ingredients from the batch seam

Phase 38 should not invent validation only at the portfolio layer. It needs row-level inputs such as:

- primary numeric target count and unit family
- requested change burden
- feasibility outcome family
- repair or provisional exposure
- difficulty and follow-through truth
- nominal vs execution-aware payoff gap
- offer-supported realized payoff participation

These row-level fields should then feed summary and breakdown artifacts.

### 3. Risk-first and distribution-aware validation breakdowns

Phase 38 should stay aligned with the portfolio reading posture from Phase 37:

- `risk_band` first
- then narrower validation lenses such as:
  - `recoverability_segment`
  - unit family
  - action family
  - offer-needed exposure when relevant

The phase should explicitly identify:

- where payoff remains strong and realism stays healthy
- where burden is high but realization is weak
- where validation pressure is driven by offer dependency
- where the numeric layer is becoming narrow, unstable, or optimistic

### 4. A business-safe validation review that is more honest than impressive

The business layer should not dump raw tables. It should answer:

- can this personalized numeric layer be trusted
- where is it credible
- where is it optimistic or unstable
- whether it became more honest but narrower

The technical layer should still preserve:

- full breakdowns
- formulas or component fields
- row-level supporting artifacts
- nominal vs execution-aware comparisons
- segment and unit-family distributions

## Recommended Plan Split

### Plan 38-01 - Canonical calibration contract and row-level validation ingredients

Focus on:

- defining the source-of-truth numeric-validation summary family
- computing realism-clean, optimism, range-stability, and carry-through signals
- exposing the row-level validation inputs from batch evaluation
- emitting validation summary and breakdown artifacts

### Plan 38-02 - Segment, distribution, and drift validation

Focus on:

- risk-band-first calibration views
- recoverability and offer-needed validation slices where useful
- unit-family and action-family distribution checks
- false-optimism and instability segment exposure
- seed or run-to-run drift and narrowness rollups in suite packaging

### Plan 38-03 - Business-safe review, KPI packaging, and regression closure

Focus on:

- business-readable validation verdict packaging
- technical-vs-business visibility split
- KPI or proof-facing validation review lines
- suite-level artifact mirroring
- regression closure across portfolio validation, batch, suite, and KPI consumers

## Main Risks

### Risk 1: Recommendation calibration gets confused with base model calibration

The repo already has classifier calibration seams. Phase 38 is about the personalized recommendation layer. If the phase drifts into model training or PD recalibration, it will reopen the wrong stack.

### Risk 2: Validation becomes a second planning engine

This phase should judge targets, burdens, and distributions. It should not modify target generation rules or feasibility semantics that were already locked in Phases 31 and 32.

### Risk 3: Small segments create fake precision

Distribution drift and instability signals can become noisy in tiny slices. The business layer should remain conservative and confidence-aware rather than overstating weak evidence.

### Risk 4: Honesty is mistaken for failure

A result like "more honest but narrower" is valid progress. Phase 38 should explicitly allow that outcome rather than forcing every validation story to look larger or cleaner than it is.

## Recommendation

Proceed with a three-part plan:

1. define one canonical calibration and validation contract
2. validate it across segment and distribution lenses
3. package the result into a business-safe review with full technical transparency underneath

That sequence matches the existing code seams and closes `CAL-01` without reopening any of the single-customer contracts already hardened in Phases 30-37.
