# Phase 34: Offer Layer Integration - Research

**Researched:** 2026-03-22
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so institution-side actions become explicit, typed, rankable offers with clear approval and acceptance semantics, while keeping the customer action story primary and preserving business-safe visibility rules?

## Planning Basis

Phase 34 now has a locked `34-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/32-feasibility-constraint-engine/32-CONTEXT.md`
- `.planning/phases/33-action-difficulty-execution-modeling/33-CONTEXT.md`
- `.planning/phases/34-offer-layer-integration/34-CONTEXT.md`
- `credit-coach/src/credit_coach/recourse/action_space.py`
- `credit-coach/src/credit_coach/recourse/offer_optimization.py`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/coaching/messaging.py`
- `credit-coach/src/credit_coach/coaching/planner.py`
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/tests/test_action_space.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`
- `credit-coach/tests/test_messaging.py`
- `credit-coach/tests/test_planner_denied_objective.py`
- `credit-coach/tests/test_portfolio_validation.py`
- `credit-coach/tests/test_phase_experiment_suite.py`

This is sufficient because Phase 34 is not inventing a new commercial layer from scratch. The repo already contains:

- institutional action templates with offer metadata
- structured offer-term generation
- offer acceptance estimation
- rankable-offer heuristics
- step-level offer narratives
- plan-level offer summaries in proof artifacts

The gap is no longer whether offers exist. The gap is whether offer truth is canonical, nested, rankable, and product-safe without collapsing into either raw metadata or standalone plan objects.

## Executive Summary

Phase 30 hardened action identity. Phase 31 hardened numeric targets. Phase 32 hardened feasibility truth. Phase 33 hardened difficulty and follow-through truth.

Phase 34 must now make institution-side support explicit.

Today the codebase already behaves as if an offer layer exists:

- `action_space.py` declares institutional templates
- `offer_optimization.py` builds terms and acceptance logic
- `schema.py` carries offer fields on `PlanAction`
- `messaging.py` can render `offer_narrative`
- runtime and proof artifacts already expose dominant offer summaries

What is still missing is one locked contract for:

1. action-level canonical `offer_contract`
2. coexistence between customer actions and institution offers
3. approval vs acceptance vs provisional vs rankable semantics
4. business-safe offer wording vs technical offer trace

Phase 34 should therefore be planned as:

`offer contract + schema hardening -> rankability and provisional semantics -> business-safe offer visibility and downstream consumer alignment`

## Existing Assets We Can Reuse

### Institutional action metadata already exists

- `credit-coach/src/credit_coach/recourse/action_space.py`
  - already defines institutional actions such as:
    - `credit_limit_adjustment`
    - `settlement_discount`
    - `installment_plan`
  - already carries:
    - `offer_type`
    - `requires_acceptance`
    - `offer_family`
    - `offer_scoring_profile`
    - `term_generation_rule`
    - `offer_policy_arm`
  - is the correct seed source for stable offer identity

### Structured offer generation already exists

- `credit-coach/src/credit_coach/recourse/offer_optimization.py`
  - already builds structured offer terms via `build_offer_contract(...)`
  - already distinguishes rankable vs non-rankable offers through approval and completeness logic
  - already estimates:
    - `offer_acceptance_probability`
    - proxy deltas
    - combined realization
  - is the natural seam for Phase 34 semantic hardening

### Schema already has most of the truth, but too flat

- `credit-coach/src/credit_coach/data/schema.py`
  - already stores offer-related fields directly on `PlanAction`
  - already has `OfferNarrative`
  - is the right seam to move from flat offer metadata to a nested canonical `offer_contract`

### Product-facing wording already has a slot

- `credit-coach/src/credit_coach/coaching/messaging.py`
  - already supports separate `offer_narrative`
  - is the main seam for:
    - keeping customer action primary
    - expressing approval vs acceptance in product-safe language
    - hiding raw scoring and policy internals from business defaults

### Runtime and proof consumers already exist

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - already serializes offer metadata into runtime artifacts
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - already depends on plan-level offer summaries
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already packages proof consumers that expect offer metrics

This means Phase 34 can stay engine-first without requiring a website redesign.

## What Phase 34 Must Deliver

### 1. Canonical nested offer contract

Phase 34 must harden:

- action-level `offer_contract`
- semi-typed canonical `offer_terms`
- derived plan-level offer summaries
- compatibility bridge from legacy flat fields to the nested contract

### 2. Clear coexistence between customer action and institution offer

Phase 34 must preserve:

- customer action as the main recovery story
- offer as a companion intervention
- one active offer branch per canonical plan
- separate offer narrative rather than blended action sentences

### 3. Approval, acceptance, and rankability semantics

Phase 34 must make explicit:

- approval pending is a supply-side gate
- acceptance pending is a customer-side realization gate
- acceptance required does not disqualify a winner
- incomplete or approval-gated offers remain provisional

### 4. Business-safe and technical-safe offer visibility

Phase 34 must ensure:

- business surfaces see explanation, rationale, summary terms, and state wording
- technical surfaces keep full contract and scoring/probability trace
- placeholder or non-executable offers do not leak into default customer-facing views

## Recommended Plan Split

### Plan 34-01 — Canonical offer contract and schema hardening

Focus on:

- nested `offer_contract` model
- semi-typed offer term contract
- legacy field compatibility and action-level source-of-truth
- runtime serialization and schema completeness

### Plan 34-02 — Rankability, provisional semantics, and derived plan summaries

Focus on:

- approval vs acceptance state semantics
- rankable-offer eligibility
- provisional-offer handling
- planner and proof alignment around derived plan-level offer truth

### Plan 34-03 — Business-safe offer visibility and downstream consumer alignment

Focus on:

- offer narrative and product wording
- technical reveal contract
- runtime and proof consumer alignment
- ensuring non-executable placeholders stay technical-only

## Main Risks

### Risk 1: Offer contract stays half-flat and drifts

If nested offer truth is introduced without a stable bridge, runtime and downstream consumers will split between old and new fields.

Mitigation:

- keep action-level source-of-truth canonical
- derive plan-level summary from that
- keep runtime serialization deterministic

### Risk 2: Approval and acceptance semantics collapse again

If approval-pending and acceptance-pending are treated the same, provisional logic and winner eligibility will remain inconsistent.

Mitigation:

- lock supply-side vs customer-side distinction in schema, ranking, and messaging

### Risk 3: Offer overwhelms the customer action story

If offer-bearing plans become commercial dumps, the product will lose the user-centered recovery path.

Mitigation:

- keep action narrative primary
- keep offer as companion block
- enforce one active offer branch

### Risk 4: Business surfaces leak raw commercial internals

If scoring profile and policy-arm metadata appear by default, product output will feel like engine diagnostics.

Mitigation:

- keep default business wording narrative-first
- limit raw contract and scoring metadata to technical reveal

## Recommendation

Proceed with Phase 34 now. The codebase already contains a working offer substrate; the correct next move is to harden it into one canonical nested contract and align ranking, runtime, messaging, and proof around that single source of truth.
