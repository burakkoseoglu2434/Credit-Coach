# Phase 15: Policy Optimization Layer - Research

**Researched:** 2026-03-16
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so Credit Coach can represent, rank, and evaluate institution-side offers beside user-driven recourse actions without weakening the governance stack built in Phases 8-14?

## Planning Basis

Phase 15 now has a locked `15-CONTEXT.md`. For this planning pass, the authoritative sources are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/research/v1.2-RECOMMENDATION-QUALITY-HARDENING.md`
- `.planning/phases/12-action-realism-feasibility-expansion/12-CONTEXT.md`
- `.planning/phases/12-action-realism-feasibility-expansion/12-RESEARCH.md`
- `.planning/phases/13-behavior-aware-recourse/13-CONTEXT.md`
- `.planning/phases/13-behavior-aware-recourse/13-RESEARCH.md`
- `.planning/phases/14-sequential-recourse-planning/14-CONTEXT.md`
- `.planning/phases/14-sequential-recourse-planning/14-RESEARCH.md`
- `.planning/phases/15-policy-optimization-layer/15-CONTEXT.md`
- current recommendation code under `credit-coach/src/credit_coach/`
- current tests under `credit-coach/tests/`

That is sufficient because the milestone contract and the Phase 15 gray-area decisions are now both locked. The remaining work is brownfield planning against the existing typed-action, probability, trajectory, batch-evidence, challenger, and outcome-feedback seams.

## Executive Summary

Phase 15 should be treated as an offer-layer extension of the current recourse engine, not a second planner stack. The repo already has most of the prerequisites:

- Phase 12 turned institutional actions into explicit typed actions with approval and constraint semantics
- Phase 13 added distinct action and plan execution likelihood
- Phase 14 made trajectories canonical and short-term-first under inherited governance gates
- outcome feedback already computes the business proxy trio:
  - `approval_rate`
  - `default_rate_90d`
  - `avg_margin_90d`
- suite, challenger, and release review already know how to consume machine-readable supporting evidence

What is missing is the institution-side offer layer:

- term-bearing offers are not yet first-class actions
- offer acceptance is not yet modeled separately from customer action execution
- recovery-aware ranking is not yet integrated into the planner
- policy arms cannot yet cleanly express offer-policy profiles
- there is no canonical `offer_optimization_summary.json` artifact

The right implementation strategy is:

- keep offers inside the existing `action_class = institutional` family, but add an explicit `offer_type` and `offer_terms` layer
- let mixed plans combine customer actions with at most one active offer branch
- model `offer_acceptance_probability` separately from `plan_execution_probability`
- compute `combined_plan_realization_probability` only for offer-bearing plans
- keep ranking governance-first:
  - inherited gates first
  - then nominal feasibility and short-term trajectory health
  - then `expected_recovery_proxy`
- publish offer optimization as mandatory supporting evidence rather than as a new acceptance gate

The locked context makes that precise:

- rankable offers need explicit terms plus explicit approval state
- term-incomplete or approval-ambiguous institutional actions remain provisional non-winner evidence
- recovery impact is evaluated over the canonical proxy trio:
  - `approval_rate`
  - `default_rate_90d`
  - `avg_margin_90d`
- internal optimizer weighting is allowed, but review and artifacts stay metric-by-metric
- policy-arm reporting must explain what offer policy changed, not only that a treatment arm exists

## Existing Assets We Can Reuse

### Institutional action templates already exist

- `credit-coach/src/credit_coach/recourse/action_space.py`
  - already defines institutional templates such as:
    - `settlement_discount`
    - `installment_plan`
    - `credit_limit_adjustment`
  - already carries conflict semantics between institutional actions

This is the natural seam for promoting selected institutional actions into explicit offer-bearing actions.

### The schema already carries typed actions, probabilities, trajectories, and policy-arm metadata

- `credit-coach/src/credit_coach/data/schema.py`
  - already carries typed-action metadata
  - already carries behavior-aware probability fields
  - already carries trajectory and `policy_arm` fields

Phase 15 therefore does not need a second plan contract. It can extend the existing one with offer terms and offer-specific probability fields.

### The planner already has the right ordering seam

- `credit-coach/src/credit_coach/coaching/planner.py`
  - already applies constraint, safety, and governance filters first
  - already uses behavior-aware and phase-aware ranking signals

Phase 15 can therefore add recovery-aware ordering below the existing gates rather than inventing a separate offer optimizer outside the planner.

### Recovery proxy math already exists in the repository seam

- `credit-coach/src/credit_coach/storage/repository.py`
  - already computes canonical proxy deltas for:
    - `approval_rate`
    - `default_rate_90d`
    - `avg_margin_90d`
  - already translates proxy deltas into treatment-vs-control outcome summaries

That makes repository the right place to reuse and normalize recovery-proxy semantics rather than re-deriving them ad hoc in the planner or CLI layer.

### Outcome feedback and review seams are already machine-readable

- `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`
  - already emits machine-readable policy-arm and proxy-delta artifacts
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already renders explanation-first review sections
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already aggregates seeded supporting evidence
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already compares variants across seeded summaries

Phase 15 should extend this evidence chain rather than opening a parallel review or reporting regime.

## Gaps Phase 15 Must Close

### 1. There is no explicit offer-bearing action contract

Institutional actions exist, but they are still too coarse. The system cannot yet distinguish between:

- a generic institutional placeholder
- a term-bearing offer that is ready to rank
- a provisional institutional branch that still lacks explicit terms or approval state

Phase 15 must close that gap.

### 2. Recovery optimization is not yet a first-class planner objective

The planner already knows feasibility, behavior, and trajectories, but it does not yet rank plans on:

- expected recovery proxy improvement
- governance-safe offer performance
- the interaction between offer acceptance and customer action execution

Phase 15 must add that objective without weakening inherited fairness, reliability, telemetry, or trajectory governance.

### 3. Offer acceptance is still conflated with generic action follow-through

Phase 13 introduced execution likelihood, but customer action execution and institution-side offer acceptance are different real-world behaviors. Phase 15 must keep them distinct and combine them only when necessary for offer-bearing plans.

### 4. There is no canonical offer optimization artifact

Batch, suite, challenger, and review flows already understand evidence artifacts, but there is no Phase 15 artifact that answers:

- how often offer-bearing plans appear
- how often offers are rankable
- what offer types dominate
- whether offers improve recovery proxies safely
- which policy arm changed offer behavior

Phase 15 must publish that evidence under one stable contract.

## Context-Locked Interpretation For Phase 15

### Phase 15 is an optimizer extension, not a new governance layer

Offer optimization is mandatory supporting evidence, but it is non-blocking. It can improve ranking and review quality, but it must not become a second acceptance or release gate.

### Offer-bearing plans must still look like one coherent trajectory

The plan model already has typed actions, execution likelihood, and canonical `phases[]`. Offer optimization must fit inside that model so a reviewer can interpret one mixed trajectory:

- customer-driven steps
- plus one explicit institution-side offer branch

### Recovery objective remains explainable

The optimizer may use a composite internally, but machine-readable evidence and markdown review must stay metric-by-metric. Phase 15 should never hide proxy trade-offs behind a single opaque score.

### Policy-arm semantics need to become richer without breaking treatment-vs-control reporting

Outcome feedback can keep the existing treatment-vs-control language, but artifacts must now explain the meaning of each policy arm through fields such as:

- `offer_family`
- `scoring_profile`
- `term_generation_rule`

## Recommended Architecture

### A. Extend institutional actions into explicit offer-bearing actions

The safest direction is to preserve:

- `action_class = institutional`

and layer on:

- `offer_type`
- `offer_terms`
- `offer_terms_complete`

That keeps the action stack stable while making offers explicit and rankable.

### B. Keep plan execution and offer acceptance distinct

Phase 13 already established `plan_execution_probability`. Phase 15 should add:

- `offer_acceptance_probability`

and compute:

- `combined_plan_realization_probability`

only for offer-bearing plans. That avoids conflating customer effort with institution-side offer uptake.

### C. Add recovery-aware ordering under the existing gate-first planner

`coaching/planner.py` should evaluate offer-bearing plans only after inherited governance and trajectory filters pass. Recovery logic should therefore sit below:

- fairness
- reliability
- telemetry
- action realism
- trajectory health

and then prefer governance-safe recovery improvement.

### D. Publish batch-owned canonical offer evidence

The canonical Phase 15 artifact should be:

- `offer_optimization_summary.json`

with companion breakdowns:

- `offer_type_breakdown.csv`
- `offer_policy_arm_breakdown.csv`
- `offer_acceptance_breakdown.csv`
- `offer_proxy_impact_breakdown.csv`

Batch should own production of these artifacts first, and suite or challenger should aggregate them in the same way they already aggregate candidate-quality, behavior-aware, and trajectory evidence.

### E. Keep review explanation-first

`kpi_contract.py` and milestone review should expose a short `Offer Optimization Summary` section that answers:

- how much of the plan mix uses offers
- whether offers are actually rankable
- whether offers are likely to be accepted
- whether combined realization is strong enough
- whether proxy deltas are governance-safe
- which offer type dominates

without turning the review surface into a dashboard.

## Recommended Plan Breakdown

### Plan 15-01: Offer action integration

Focus on extending the typed institutional action family into explicit offer-bearing actions with structured offer terms and mixed-plan semantics.

### Plan 15-02: Recovery-aware offer scoring

Focus on integrating recovery proxies, offer acceptance probability, and governance-safe offer ranking into the existing planner and batch evidence seams.

### Plan 15-03: Offer-policy evidence and review integration

Focus on seeded suite aggregation, challenger comparison, richer policy-arm semantics, outcome-feedback compatibility, and explanation-first review output.

## Risks To Watch

- building a parallel offer optimizer that drifts from the existing planner and trajectory stack
- letting recovery or margin upside override inherited governance gates
- collapsing offer acceptance into plan execution probability and losing interpretability
- allowing multiple competing active offers in one winner plan
- emitting offer-policy evidence only in markdown instead of machine-readable artifacts

## Recommendation

Proceed with Phase 15 now. The brownfield seams are ready: institutional actions already exist, behavior-aware probability already exists, trajectories are already canonical, and business proxy deltas are already computed. Phase 15 is the natural point to convert those building blocks into a true offer-policy optimization layer without reopening the governance contract.
