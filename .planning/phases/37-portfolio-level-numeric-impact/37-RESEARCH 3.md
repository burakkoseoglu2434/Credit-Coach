# Phase 37: Portfolio-Level Numeric Impact - Research

**Researched:** 2026-03-22
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so Credit Coach can aggregate personalized numeric plans into portfolio-level business impact that is honest about requested change, execution realism, offer dependency, and realized payoff without reopening single-customer contracts?

## Planning Basis

Phase 37 now has a locked `37-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/17-full-portfolio-evaluation-coverage-audit/17-CONTEXT.md`
- `.planning/phases/19-behavior-aware-recourse/19-CONTEXT.md`
- `.planning/phases/34-offer-layer-integration/34-CONTEXT.md`
- `.planning/phases/37-portfolio-level-numeric-impact/37-CONTEXT.md`
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
- `credit-coach/tests/test_portfolio_validation.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach/tests/test_kpi_contract.py`

This is sufficient because Phase 37 is not changing:

- action identity
- numeric target generation
- feasibility semantics
- execution modeling
- offer semantics
- single-customer narrative or UI contracts

The repo already contains portfolio aggregation seams. The open work is to add one explicit numeric-impact layer on top of those seams.

## Executive Summary

Phase 17 established full-cohort proof. Phase 19 hardened execution-aware truth. Phase 34 clarified offer dependency. Phase 36 locked the product surface as a strict consumer.

Phase 37 now needs to answer a more specific portfolio question:

- how much numeric change are we asking from the cohort
- how much of that change is realistically realizable
- where offer support is carrying the result
- what the execution-aware payoff actually looks like

The codebase already has most of the raw ingredients:

- portfolio validation aggregates coverage, reality-gap, offer, trajectory, and behavior truth
- batch eval writes plan-level execution, difficulty, and combined realization fields
- suite packaging already mirrors portfolio validation, behavior, and offer summaries
- KPI review already renders portfolio-facing evidence for proof and release-style summaries

What is still missing is one locked family of portfolio numeric-impact metrics:

1. headline numeric impact cards
2. normalized burden for mixed-unit requested change
3. execution-aware vs nominal payoff pair
4. offer-supported realized payoff story
5. executive segment insight around payoff vs burden vs realization

Phase 37 should therefore be planned as:

`numeric-impact contract -> segment/execution-aware aggregation -> business-vs-technical review and suite alignment`

## Existing Assets We Can Reuse

### Portfolio validation already owns the portfolio proof seam

- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - already computes:
    - coverage funnel
    - reality-gap summaries
    - segment breakdowns
    - offer diagnostics
    - behavior comparisons
    - trajectory class breakdowns
  - already renders review markdown
  - is the natural seam for canonical numeric-impact summary additions

### Batch evaluation already writes the necessary per-customer ingredients

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already carries fields such as:
    - `best_plan_execution_probability`
    - `best_mean_group_difficulty_score`
    - `best_combined_plan_realization_probability`
    - offer summary fields
    - execution scenario outputs
  - already emits portfolio validation artifacts into run tables
  - is the right seam for adding per-row numeric-impact helpers and derived CSV exports

### Suite packaging already mirrors phase-level portfolio artifacts

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already aggregates:
    - portfolio validation summary
    - behavior-aware summary
    - offer summary
    - segment and breakdown tables
  - is the natural seam for seed-level and scale-level numeric-impact rollups

### KPI review already knows how to tell a business-first story

- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already presents behavior-aware and offer-aware review lines
  - can absorb a new portfolio numeric-impact narrative without becoming the source of truth

## What Phase 37 Must Deliver

### 1. A canonical portfolio numeric-impact metric family

The locked business headline must be exactly:

- `numeric_plan_coverage`
- `requested_change_burden`
- `execution_aware_realization`
- `execution_aware_portfolio_payoff`

The locked supporting business metrics must include:

- `realization_gap`
- `offer_supported_realization_share`

The technical layer must also preserve:

- `nominal_portfolio_payoff`
- `execution_aware_portfolio_payoff`
- `nominal_offer_supported_payoff`
- `realized_offer_supported_payoff`
- `payoff_per_unit_burden`

### 2. Mixed-unit requested change must become one honest portfolio burden story

Phase 37 cannot report raw averages of:

- currency deltas
- percentage-point deltas
- score-point deltas

as if they were one coherent scalar.

So this phase must introduce:

- a normalized requested change burden index for business reading

while preserving:

- raw unit-family distributions
- metric-family tables

for technical inspection.

### 3. Execution-aware truth must dominate the portfolio claim

Phase 37 must carry both:

- nominal payoff
- execution-aware payoff

But the primary portfolio claim should be execution-aware. The difference between the two should be explicit as:

- `realization_gap`

This is the key honesty guardrail that prevents the new numeric layer from looking stronger on paper than it is in practice.

### 4. Segment insight must stay executive, not tabular

The business layer should not dump a segment cube. It should answer:

- where do we get the highest payoff
- where are we asking the most but realizing the least
- where is institution support doing the most work

The locked segment priorities are:

- `risk_band` first
- `recoverability_segment` second
- `offer_needed_segment` for offer dependency

## Recommended Plan Split

### Plan 37-01 — Canonical numeric-impact contract and batch artifact seam

Focus on:

- defining the new canonical portfolio numeric-impact metric family
- computing normalized requested change burden
- adding nominal vs execution-aware portfolio payoff pair
- emitting a new portfolio numeric-impact summary and breakdown artifact family from batch eval and portfolio validation

### Plan 37-02 — Segment insight and execution-aware aggregation hardening

Focus on:

- risk-band-first portfolio impact breakdowns
- recoverability and offer-needed segment rollups
- highest-payoff vs highest-burden/lowest-realization outputs
- realized offer-supported payoff treatment
- payoff-per-unit-burden and realization-gap segment comparisons

### Plan 37-03 — Business review, KPI contract, and suite/proof alignment

Focus on:

- business-safe headline/supporting metric packaging
- technical vs business visibility split
- suite-level numeric-impact rollups
- KPI review and proof-facing integration
- regression closure across portfolio validation, suite packaging, and KPI consumers

## Main Risks

### Risk 1: Burden becomes a fake scalar

If Phase 37 averages mixed units directly, the headline burden metric will look precise but mean very little.

Mitigation:

- normalize requested change burden explicitly
- keep raw unit-family distributions technical

### Risk 2: Portfolio claims drift back to nominal optimism

If nominal payoff is allowed to dominate review copy, the new personalized numeric layer will overstate real value.

Mitigation:

- keep execution-aware payoff primary
- make realization gap explicit and visible

### Risk 3: Offer support muddies customer-side payoff truth

If offer-supported impact is blended into the overall payoff without separation, users will not know whether value comes from customer behavior or institution-side help.

Mitigation:

- carry nominal and realized offer-supported payoff separately
- emphasize realized offer-supported payoff in business review

### Risk 4: Segment reporting becomes a data dump

If the segment layer becomes exhaustive rather than prioritized, the business signal will disappear.

Mitigation:

- lock executive segment outputs
- keep detailed segment tables in the technical layer only

## Recommendation

Proceed with Phase 37 now. The codebase already has the right portfolio seams; what is missing is a disciplined numeric-impact layer that converts personalized plan truth into cohort-level business value without sacrificing honesty.
