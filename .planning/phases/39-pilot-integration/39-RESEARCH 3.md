# Phase 39: Pilot Integration - Research

**Researched:** 2026-03-22
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so the personalized planning stack can run against institution-style pilot data bundles, emit a trustworthy pilot package, and support operator onboarding without pretending that live external integrations already exist?

## Planning Basis

Phase 39 does not yet have a locked `39-CONTEXT.md`. For this planning pass, the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/25-pilot-readiness-demo-ops-baseline/25-CONTEXT.md`
- `.planning/phases/25-pilot-readiness-demo-ops-baseline/25-RESEARCH.md`
- `.planning/phases/31-numeric-target-engine/31-CONTEXT.md`
- `.planning/phases/34-offer-layer-integration/34-CONTEXT.md`
- `.planning/phases/35-narrative-generation-v2/35-CONTEXT.md`
- `.planning/phases/37-portfolio-level-numeric-impact/37-CONTEXT.md`
- `.planning/phases/38-calibration-validation/38-RESEARCH.md`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/ops/release_decision.py`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
- `credit-coach-website/PILOT_READINESS.md`
- `credit-coach-website/CURATED_DEMO_HANDOFF.md`
- `credit-coach-website/shared/content-schema.ts`
- `credit-coach-website/server/storage/inbound.ts`

This is sufficient because the user explicitly requested planning before a discuss pass, and Phase 39 should not reopen the single-customer contracts already locked in Phases 30-38. The missing work is pilot seam hardening, not action, target, feasibility, narrative, or UI semantics.

## Executive Summary

The repo already has most of the ingredients needed for a serious pilot seam:

- personalized semantic, numeric, feasibility, execution, offer, and narrative truth
- portfolio proof, calibration, and product confidence packaging
- pilot-readiness and curated demo handoff docs on the website side
- release and smoke semantics that already expose `pilot_eligible`, `acceptance_status`, and `pilot_guardrails`

What is still missing is one explicit bridge from institution-style data to the personalized planning loop.

Today, the system can:

- accept structured demo and pilot intake from the website
- render buyer-safe and analyst-safe artifacts
- evaluate personalized plans on synthetic or milestone-local cohorts

But it still lacks:

- one canonical pilot input contract for institution-style exported data
- one runner that validates that input contract and turns it into engine-owned personalized artifacts
- one operator-facing output package that says what was run, what was emitted, and whether the result is pilot-eligible

Phase 39 should therefore be planned as:

`pilot input contract -> pilot package runner and guardrails -> onboarding and handoff docs`

## Existing Assets We Can Reuse

### Pilot-readiness baseline already exists on the website side

- `credit-coach-website/PILOT_READINESS.md`
- `credit-coach-website/CURATED_DEMO_HANDOFF.md`

These already define:

- controlled pilot posture instead of full production posture
- structured intake fields such as:
  - `institutionType`
  - `portfolioFocus`
  - `demoTrack`
  - `timeline`
  - `dataReadiness`
- operator-mediated handoff and proof-first trust cues

Phase 39 should build on this, not replace it.

### Portfolio, proof, and pilot guardrail seams already exist

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/ops/release_decision.py`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`

These already emit or consume:

- `pilot_guardrails.json`
- `acceptance_status`
- `pilot_eligible`
- portfolio validation and product confidence artifacts

This means Phase 39 does not need to invent a second pilot truth system. It needs to package the existing truth stack into a pilot-run contract.

### Batch and portfolio evaluation already provide the engine core

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`

These already know how to produce:

- personalized plan outputs
- numeric impact summaries
- calibration and validation summaries
- portfolio review and proof-facing artifacts

Phase 39 should use them as the pilot engine core rather than creating a parallel evaluator.

## What Phase 39 Must Deliver

### 1. One canonical pilot input contract

Phase 39 should define one typed institution-style data contract that is strict enough to validate:

- borrower or account identity
- model-required planning inputs
- optional institution metadata
- mapping or provenance information

The key guardrail:

- one exported-bundle contract, not bespoke institution hardcoding

This contract should fail closed if required fields are missing or unmappable.

### 2. One pilot runner that preserves engine-owned truth

The phase needs one canonical runner that:

- validates the pilot bundle
- normalizes it into the planning loop
- runs personalized planning without reopening v2.0 semantics
- emits one pilot package with:
  - manifest and provenance
  - personalized plan outputs
  - portfolio validation summary
  - calibration validation summary
  - product confidence or pilot guardrails

This runner should behave as a consumer and orchestrator of the existing engine seams, not a new planner.

### 3. One operator-facing pilot package and onboarding path

Phase 39 should make pilot onboarding explicit enough that an operator can answer:

- what input shape is accepted
- how a pilot run is executed
- what artifacts are emitted
- how pilot eligibility and watchlist posture are read
- how website-side buyer handoff and engine-side pilot package relate

This is the point where Phase 25’s pilot-readiness posture and v2.0’s personalized planning stack finally meet.

## Recommended Phase Split

### Plan 39-01 - Canonical pilot data contract and validation seam

Focus on:

- defining the institution-style input bundle
- validating mappings and required fields
- creating one pilot manifest and ingestion entry point
- documenting the pilot data contract

### Plan 39-02 - Pilot package runner and guardrail packaging

Focus on:

- running the personalized planning loop over a validated pilot bundle
- emitting one pilot package with manifest, portfolio proof, calibration, and guardrails
- making pilot eligibility and acceptance status explicit and reproducible

### Plan 39-03 - Pilot onboarding, docs, and handoff alignment

Focus on:

- documenting how operators run and inspect the pilot package
- aligning website pilot-readiness and curated demo handoff docs with the new engine-owned pilot package
- keeping the posture honest about controlled pilot scope versus deferred live integrations

## Main Risks

### Risk 1: Phase 39 drifts into live integration work

This phase should not attempt:

- live CRM sync
- LOS integration
- auth rollout
- external API onboarding

It should create one explicit pilot seam that can be exercised offline or against institution-style exported data.

### Risk 2: Pilot packaging becomes a second source of truth

If the pilot runner invents its own semantics for payoff, guardrails, or narratives, the engine and product will drift.

Mitigation:

- the pilot package must reuse existing engine-owned artifacts and release semantics

### Risk 3: Institution-style input becomes too vague

If the input contract accepts arbitrary exports without a strict mapping and provenance contract, trust will collapse during onboarding.

Mitigation:

- validate required fields
- record mapping provenance
- fail closed on missing mandatory inputs

### Risk 4: Docs overclaim full production maturity

The correct story is:

- controlled pilot seam
- explicit operator ownership
- explicit output package

Not:

- full live deployment readiness

## Recommendation

Proceed with a three-part plan:

1. define one canonical pilot data contract and validated ingestion seam
2. build one pilot package runner that reuses the personalized planning and guardrail stack
3. document the onboarding and handoff path so buyers and operators can trust the integration boundary

That is enough to close `PILT-01` without reopening any of the customer-level contracts already hardened in Phases 30-38.
