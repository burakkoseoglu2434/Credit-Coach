# Phase 44: Production Pilot Baseline - Research

**Researched:** 2026-03-23
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that turns the shipped deterministic decision stack into a repeatable, QA-gated, institution-configurable production-pilot baseline without creating a second engine or leaking internal-only truth?

## Planning Basis

Phase 44 decisions were discussed in-session and are now locked in [44-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/44-production-pilot-baseline/44-CONTEXT.md). For this planning pass the authoritative inputs are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [44-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/44-production-pilot-baseline/44-CONTEXT.md)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [run_pilot_integration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_integration.py)
- [run_production_smoke.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_production_smoke.py)
- [release_decision.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/release_decision.py)
- [contracts.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/pilot/contracts.py)
- [engine.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/policy/engine.py)
- [PILOT_PACKAGE_SCHEMA.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_PACKAGE_SCHEMA.md)
- [PILOT_EXECUTION_GUIDE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_EXECUTION_GUIDE.md)
- [PILOT_READINESS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/PILOT_READINESS.md)

This is sufficient because the repo already has:

- deterministic decision ownership from Phase 40.5
- additive calibration and policy-version comparison outputs from Phase 41
- operator review packets and briefings from Phase 43
- explicit planner/source provenance from Phase 42
- an export-first pilot package lane from Phase 39

The missing layer is no longer decision truth. The missing layer is **repeatable pilot operation, artifact QA discipline, institution-specific runtime overlays, and institution-facing explanation packaging**.

## Executive Summary

Phase 44 should be planned as a **production-pilot operations phase**, not as a new decision or calibration phase.

The safest shape is:

`existing decision stack -> refresh orchestrator -> artifact QA lane + portfolio smoke lane -> institution-safe package + explanation pack -> bounded proof guidance`

The code scan shows five important truths:

1. [run_pilot_integration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_integration.py) already knows how to build an engine-owned pilot package, so Phase 44 should orchestrate and extend this lane rather than replace it
2. [run_production_smoke.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_production_smoke.py) already owns KPI, fairness, telemetry, and release smoke, but not artifact integrity or packet completeness
3. [contracts.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/pilot/contracts.py) already gives a typed pilot manifest seam, but it does not yet carry refresh cadence, reference-run provenance, overlay provenance, or explanation-pack references
4. [engine.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/policy/engine.py) already emits adverse-action-friendly reason payloads, which is the right bridge for a compliance-adjacent explanation pack
5. The website pilot docs already say “controlled pilot” and “not fully production”; Phase 44 should make that story more versioned and QA-gated rather than more ambitious

The clean split for this phase is therefore:

`refresh orchestration + artifact QA -> institution overlays + explanation pack -> docs/proof guidance + regression closure`

## Existing Assets We Can Reuse

### Pilot package lane already exists

- [run_pilot_integration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_integration.py)
  - already runs normalized pilot input through batch planning
  - already mirrors portfolio artifacts into a pilot package
  - already writes pilot manifests, guardrails, KPI snapshots, and release evidence

This is the right seam for:

- refreshed pilot package outputs
- policy-version packaging
- explanation-pack attachment
- overlay provenance attachment

### Release smoke lane already exists

- [run_production_smoke.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_production_smoke.py)
  - already computes portfolio and release smoke gates
  - already speaks in release-decision language

This is the right seam for:

- portfolio smoke inside refresh orchestration
- release-smoke summary packaging

### Release-decision vocabulary already exists

- [release_decision.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/release_decision.py)
  - already defines `GO`, `LIMITED_GO`, and `NO_GO`
  - already builds pilot guardrails

This is the right seam for:

- Phase 44 refresh outcome wording
- PASS / DEGRADED / FAIL alignment against pilot readiness posture

### Decision and explanation ingredients already exist

- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py)
  - already owns deterministic external and internal decision truth
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py)
  - already owns an internal-review derived surface
- [engine.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/policy/engine.py)
  - already builds adverse-action-friendly reason payloads

These are the right seams for:

- decision explanation pack generation
- drift-free operator/explanation audience split
- institution-facing non-legal explanation output

### Pilot docs already have the right honesty posture

- [PILOT_PACKAGE_SCHEMA.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_PACKAGE_SCHEMA.md)
- [PILOT_EXECUTION_GUIDE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_EXECUTION_GUIDE.md)
- [PILOT_READINESS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/PILOT_READINESS.md)

These are the right seams for:

- policy-versioned refresh guidance
- bounded proof-surface wording
- “controlled pilot baseline” messaging

## Concrete Repo Findings

### 1. Repeatable pilot operation is still implicit

The repo can already produce:

- collection runs
- calibration outputs
- operator packets
- pilot packages
- smoke summaries

But the refresh discipline that ties these into one repeatable “pilot baseline refresh” is still operator memory and ad hoc command ordering.

### 2. Artifact trust and portfolio smoke are still mixed conceptually

Today there is a strong release/smoke lane and a strong artifact-production lane, but there is no explicit “artifact QA” contract that says:

- package is complete
- parity-safe outputs are present
- operator packets are complete
- calibration subtree is complete
- internal-only states did not leak

Phase 44 should split “is the pilot package trustworthy?” from “does the portfolio smoke still pass?”.

### 3. Institution-specific runtime posture is not first-class yet

The repo already has pilot bundle institution context, but not a thin runtime overlay layer that says:

- this institution’s usage posture
- this institution’s enabled offer families
- this institution’s pilot traffic or refresh posture

That means the repo can run a pilot package, but not yet replay a pilot baseline with explicit institution-specific runtime provenance.

### 4. Operator packet and institution-facing explanation pack are not yet separated by audience

The repo already has:

- deterministic decision truth
- operator packet
- adverse-action-friendly reason hints

But not yet a distinct institution-facing explanation pack with:

- external-only decision truth
- audit-friendly decision summary
- upgrade path and readiness
- governance and QA stamps
- clear “not legal advice / not compliance automation” boundary

### 5. The right honest story is already present; it just needs packaging

The website docs already avoid overclaiming. Phase 44 should reinforce that with:

- versioned refresh status
- QA status
- portfolio smoke status
- bounded vocabulary

instead of inventing a larger “production-ready” claim.

## What Phase 44 Must Deliver

### 1. A new refresh orchestrator over existing runners

Phase 44 should add one orchestration CLI that:

- runs the collection lane
- refreshes pilot package artifacts
- runs artifact QA and portfolio smoke
- writes refresh manifests and comparison summaries

without changing decision ownership logic.

### 2. A dedicated pilot artifact QA lane

Phase 44 should add a new QA runner that checks:

- completeness
- trust and parity
- packaging integrity
- calibration completeness
- operator packet completeness

and returns `PASS | DEGRADED | FAIL`.

### 3. Thin institution overlay config contracts

Phase 44 should introduce:

- `institution_policy.yaml`
- `institution_offer.yaml`
- optional `pilot_profile.yaml`

with deterministic precedence and refresh-manifest provenance.

### 4. A decision explanation pack

Phase 44 should add an institution-facing explanation artifact that stays tied to the same decision truth as operator packets, but speaks to a different audience.

### 5. Production-pilot docs and proof guidance

Phase 44 should update pilot docs and proof guidance so the repo can say:

- deterministic and versioned
- repeatable refresh
- QA-gated package
- bounded pilot-safe claim

without saying:

- live integrated
- self-serve
- compliance automation
- autonomous adjudication

## Recommended Plan Split

### Plan 44-01 — Refresh orchestrator and artifact QA lane

Focus on:

- `run_pilot_baseline_refresh`
- `run_pilot_artifact_qa`
- refresh manifest and summary outputs
- portfolio smoke + artifact QA dual-lane reporting

### Plan 44-02 — Institution overlays and explanation-pack packaging

Focus on:

- typed overlay contract and precedence
- refresh-time resolved config provenance
- decision explanation pack
- operator/explanation drift guards

### Plan 44-03 — Pilot docs, proof guidance, and regression closure

Focus on:

- pilot package schema and execution guide updates
- website pilot-readiness and handoff guidance updates
- versioned refresh / QA / bounded pilot wording
- end-to-end regression closure for the new refresh lane

## Risks To Avoid

- Do not add a second decision engine inside the refresh orchestrator
- Do not let artifact QA become a hidden decision-policy override
- Do not turn institution overlays into live integration scope
- Do not let explanation pack and operator packet drift in reasons, readiness, or upgrade path
- Do not let proof surfaces expose `NEEDS_REVIEW`, raw gate trace, or debug internals

## Smallest Safe Implementation

The smallest safe Phase 44 implementation is:

1. add refresh orchestration over current collection/pilot/smoke runners
2. add dedicated artifact QA with explicit PASS / DEGRADED / FAIL contract
3. add thin institution overlays and materialize resolved config provenance
4. add explanation pack derived from the owned decision payload
5. update pilot/proof docs to reflect versioned, repeatable, bounded pilot truth

That is enough to satisfy `PROD-01` and `PROD-02` without reopening earlier milestone phases.
