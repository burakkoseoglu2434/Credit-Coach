# Phase 19: Behavior-Aware Recourse - Research

**Researched:** 2026-03-19
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so the already shipped behavior-aware layer stays believable under full-cohort proof and product scrutiny, especially when theoretical uplift conflicts with realistic follow-through?

## Planning Basis

Phase 19 now has a locked `19-CONTEXT.md`. For this planning pass, the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/19-behavior-aware-recourse/19-CONTEXT.md`
- `.planning/phases/13-behavior-aware-recourse/13-CONTEXT.md`
- `.planning/phases/17-full-portfolio-evaluation-coverage-audit/17-CONTEXT.md`
- `.planning/phases/18-decision-narrative-product-output-translation/18-CONTEXT.md`
- `credit-coach/src/credit_coach/recourse/execution_probability.py`
- `credit-coach/src/credit_coach/coaching/planner.py`
- `credit-coach/src/credit_coach/coaching/loop.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_planner_denied_objective.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach/tests/test_portfolio_validation.py`

This is sufficient because Phase 19 is not inventing a new execution model from scratch. The codebase already has a canonical execution-probability seam, weekly execution loop, planner integration, and behavior-aware artifacts. The remaining work is to harden their posture, ranking influence, composite semantics, and executive evidence.

## Executive Summary

The brownfield behavior-aware stack already exists and works, but it still behaves too much like a first-pass heuristic layer:

- `execution_probability.py` already estimates action and plan likelihoods
- `planner.py` already uses expected PD improvement in ranking
- `loop.py` already acts as the canonical weekly execution seam
- batch, suite, challenger, and portfolio validation already consume behavior-aware outputs

The gap is not missing capability. The gap is credibility under stronger scrutiny:

1. the estimator is not yet explicitly conservative when burden and horizon interact
2. ranking still needs stronger execution-aware demotion semantics
3. composite and provisional branches need a clearer realization model
4. executive proof should center on nominal-vs-execution-aware divergence rather than only reporting raw execution fields

Phase 19 should therefore be planned as a hardening pass over existing seams, not as a rebuild of Phase 13.

## Existing Assets We Can Reuse

### The execution-probability seam already exists

- `credit-coach/src/credit_coach/recourse/execution_probability.py`
  - already computes:
    - `action_execution_probability`
    - `plan_execution_probability`
    - grouped probabilities
    - approval-dependent probabilities
    - `expected_pd_improvement`
  - already contains:
    - class anchors
    - burden-like penalties
    - time penalties
    - customer-context adjustment

This is the correct seam for conservative bias tuning, burden-horizon interaction penalties, composite aggregation changes, and dual-realization output.

### Planner already has the correct insertion point

- `credit-coach/src/credit_coach/coaching/planner.py`
  - already ranks after gate and eligibility filters
  - already separates:
    - status priority
    - constraint priority
    - trajectory policy
    - expected improvement terms

This means Phase 19 can intensify execution-aware demotion without violating the locked gate-first contract.

### Weekly execution truth already exists

- `credit-coach/src/credit_coach/coaching/loop.py`
  - already emits:
    - `execution_rate`
    - execution scenario
    - missed-action evidence
    - trajectory status and replan behavior

Phase 19 should continue to treat this loop as canonical and align the hardening pass with it rather than creating a second simulation interpretation.

### Behavior-aware proof surfaces already exist

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already emits:
    - `behavior_aware_summary.json`
    - `execution_probability_breakdown.csv`
    - `partial_execution_breakdown.csv`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already aggregates behavior-aware evidence across seeds
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - already consumes execution-aware fields in full-cohort proof
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already renders behavior-aware evidence in review language

This is important because Phase 19 can change what these artifacts emphasize without inventing a new artifact family.

## What Phase 19 Must Deliver

### 1. Conservative-but-balanced probability posture

The locked context now makes this explicit:

- default posture is balanced
- bias is mildly conservative
- burden plus horizon interaction is the strongest penalty
- ambiguous cases should default low, not high
- limited context lifts are allowed, but must stay bounded
- the governing product principle is:
  - avoid false optimism

This means the estimator should stop behaving like a neutral scoring helper and start behaving like a trust-preserving realism layer.

### 2. Stronger ranking leverage

Phase 13 established expected utility as non-gating ranking evidence. Phase 19 now sharpens the leverage:

- low execution probability should cause strong demotion
- execution-aware improvement should dominate nominal improvement when they conflict
- high-risk or denied populations should be even more execution-aware
- the winner concept is no longer “best theoretical plan”
- it is:
  - the plan that can be defended in the product with confidence

### 3. Cleaner composite and provisional semantics

The current code already distinguishes executable and approval-dependent actions, but Phase 19 needs a more explicit model:

- composite groups should use a weighted min-average hybrid
- plans can carry both:
  - executable realization
  - approval-dependent realization
- provisional or approval-pending plans may still contend, but must be penalized hard
- offer presence must not erase action burden

This is a modeling hardening pass, but it also affects downstream narrative and proof truth.

### 4. More decision-ready evidence

Phase 19 should make behavior proof more product-relevant. The locked emphasis is now:

- primary comparison:
  - nominal improvement vs execution-aware improvement
- primary executive risk sentence:
  - high uplift but low follow-through
- primary default segment lens:
  - `risk_band`
- default buyer/demo question:
  - how much of this plan is realistically executable?

So the artifact family should stop feeling like a raw behavior dump and start feeling like an explanation of realistic plan value.

## Recommended Plan Split

The cleanest split is still three plans, but unlike historical Phase 13 they should be framed as hardening waves.

### Plan 19-01 — Probability posture and realization contract

Focus on:

- conservative execution estimator tuning
- burden-plus-horizon interaction penalties
- explicit low-default behavior under ambiguity
- composite weighted min-average aggregation
- dual realization layers for executable vs approval-dependent branches

This is the foundation because the rest of the phase depends on stable truth inputs.

### Plan 19-02 — Ranking leverage and contender behavior

Focus on:

- strong execution-aware demotion
- execution-aware dominance over nominal improvement in conflicts
- stronger execution-aware behavior inside high-risk or denied populations
- provisional contender penalties that do not remove visibility but do reduce credibility

This is where the phase turns trust preferences into winner-selection behavior.

### Plan 19-03 — Evidence, review, and cohort-facing emphasis

Focus on:

- making nominal-vs-execution-aware comparison the primary artifact and review story
- risk-band-first behavior breakdowns
- stronger executive review sentences
- suite, KPI, and portfolio-proof surfaces consuming the hardened behavior truth cleanly

This is how Phase 19 becomes visible beyond the planner itself.

## Main Risks

- making the estimator so conservative that it collapses coverage rather than improving realism
- over-penalizing provisional contenders until useful branches disappear from evidence entirely
- creating a second implicit realization model in review code instead of keeping truth centralized
- hardening ranking without also updating the proof surfaces, which would leave the new behavior invisible

## Recommendation

Proceed with Phase 19 now. The repo already has the correct code seams and test coverage for a hardening pass. The right move is not to rebuild behavior-aware recourse, but to make it more conservative, more ranking-relevant, and more executive-readable in exactly the places Phase 17 and Phase 18 exposed as weak.
