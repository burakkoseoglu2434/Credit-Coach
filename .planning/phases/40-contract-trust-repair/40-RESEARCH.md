# Phase 40: Contract & Trust Repair - Research

**Researched:** 2026-03-23
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so single-customer and collection artifacts become null-free, parity-safe, zero-step-safe, and trustworthy enough to carry final decision truth before Phase 40.5 adds the full deterministic decision policy?

## Planning Basis

Phase 40 now has a locked `40-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/40-contract-trust-repair/40-CONTEXT.md`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`
- `credit-coach-website/server/services/live-demo.ts`
- `credit-coach-website/shared/demo-schema.ts`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_customer_artifact_collection.py`

This is sufficient because Phase 40 is not inventing a new decision layer. The repo already has:

- one raw single-customer artifact seam in `run_recourse.py`
- one collection artifact seam in `run_customer_artifact_collection.py`
- one existing raw summary block that already carries some decision truth
- one website live consumer that already expects those fields, but still falls back to weaker legacy status paths

The gap is not missing serialization machinery. The gap is that the contract is incomplete, partly duplicated, and still leaky under nulls, parity drift, and zero-step winners.

## Executive Summary

Phase 40 should be planned as a trust-repair phase, not a policy-design phase.

The current code already produces the right artifact families:

- `customer_roadmap.json`
- `metrics.json`
- `customer_roadmap_steps.csv`
- `customer_metrics.csv`
- `customer_plans.csv`
- `collection_manifest.json`
- `collection_summary.md`

But the collection evidence and code scan show four real breaks:

1. raw roadmap top-level decision fields are still missing
2. summary fields like combined or approval-dependent realization still serialize as null
3. raw and flat contracts are built by separate code paths without one shared parity gate
4. zero-step best outcomes still survive into the artifact lane

The clean split for Phase 40 is therefore:

`raw contract normalization -> flat parity and contract health -> zero-step enforcement and consumer trust alignment`

## Existing Assets We Can Reuse

### Raw roadmap builder already exists

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `_build_customer_roadmap(...)` already emits:
    - `summary`
    - `checkpoints`
    - `phases`
    - `narrative`
  - checkpoint `status` is already present when upstream trajectory data is good
  - raw bundle writing is centralized in `write_customer_artifact_bundle(...)`

This is the right seam for:

- summary normalization
- checkpoint fallback
- zero-step detection
- raw contract-health computation

### Flat collection pipeline already exists

- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`
  - already mirrors part of raw summary into `customer_metrics.csv`
  - already builds manifest and markdown summary
  - already has deterministic customer selection and output layout

This is the right seam for:

- raw-to-flat mirroring
- parity validation
- contract-health rollups
- collection-level trust reporting

### Downstream consumer already shows the weak point

- `credit-coach-website/server/services/live-demo.ts`
  - still derives `decision_status` from `rawRoadmap.best_status ?? rawMetrics.best_status`
  - still infers realization when raw contract does not carry it cleanly

This is important because it proves the producer contract is not yet strong enough. Phase 40 does not need a UI redesign, but it should leave the live consumer able to trust `summary` as the canonical source.

## Concrete Repo Findings

The recent 50-customer collection run shows:

- raw top-level roadmap fields missing in `50/50`:
  - `decision_status`
  - `credit_readiness_stage`
  - `plan_execution_probability`
  - `approval_dependent_plan_probability`
  - `combined_plan_realization_probability`
- summary still null in `50/50` for:
  - `approval_dependent_plan_probability`
  - `combined_plan_realization_probability`
- zero-step best outcomes: `19/50`
- checkpoint `status` is already populated in sampled raw files, so Phase 40 should preserve and enforce it rather than invent a new checkpoint layer

This means Phase 40 is not speculative. The exact failure modes are already visible.

## What Phase 40 Must Deliver

### 1. One canonical source of decision truth

Raw roadmap `summary` must become the single source of truth for:

- external decision status
- internal decision status
- readiness
- execution and realization probabilities
- zero-step truth
- contract-health booleans

`contract_health` can exist, but only as a derived mirror.

### 2. Deterministic contract-safe fallback behavior

Before Phase 40.5 designs the real decision thresholds, Phase 40 still needs deterministic fallback rules:

- zero-step -> external `REJECTED`
- data issue -> external `CONDITIONAL`
- otherwise passthrough legacy status

Without this, null-freeness alone would still leave ambiguous or unstable outputs.

### 3. Raw-to-flat parity as a first-class invariant

Phase 40 must add one reusable parity gate between:

- raw roadmap
- raw metrics
- flat customer metrics
- raw roadmap steps
- flat roadmap steps

This is the heart of the trust repair. Otherwise raw and flat outputs keep drifting independently.

### 4. Zero-step winners must be killed before decision policy work

The current collection evidence proves zero-step best outcomes exist. That is not a later ranking refinement anymore; it is already a contract trust issue.

Phase 40 must therefore enforce:

- `best_action_count == 0` -> rejected artifact path
- step table empty only when the customer is explicitly `NO_PATH`

### 5. Contract health must be reviewable in one glance

The collection summary and manifest should answer:

- how many customers have clean contracts
- how many have parity drift
- how many were downgraded because of data issues
- how many are zero-step rejections

## Recommended Plan Split

### Plan 40-01 — Raw contract normalization

Focus on:

- shared normalization helper
- null-free summary fields
- checkpoint fallback
- deterministic contract-safe status fallback
- raw `contract_health`

### Plan 40-02 — Flat parity and collection health

Focus on:

- mirror required summary truth into flat outputs
- parity validator
- manifest and summary contract-health rollups
- collection-level classification behavior

### Plan 40-03 — Zero-step enforcement and consumer trust alignment

Focus on:

- hard zero-step rejection
- plan-level contract flags in flat outputs
- live consumer alignment to `summary` as source-of-truth
- regression closure

## Main Risks

### Risk 1: Phase 40 quietly becomes Phase 40.5

If approval thresholds or readiness policy are redesigned here, the phase boundary breaks.

Mitigation:

- keep Phase 40 to fallback-safe status repair only
- leave normal approve or conditional semantics to Phase 40.5

### Risk 2: Two sources of truth remain

If `summary` and `contract_health` both carry live decision meaning, parity becomes harder instead of easier.

Mitigation:

- `summary` is canonical
- `contract_health` is derived only

### Risk 3: Collection health becomes descriptive only

If mismatch counts are reported but do not change customer classification, trust failures remain silent.

Mitigation:

- parity fail and missing critical truth must drive `data_issue_flag`
- external output must downgrade to `CONDITIONAL`
- internal output must upgrade to `NEEDS_REVIEW`

### Risk 4: Website keeps using legacy fallback status

If live demo still reads `best_status`, internal-only states may continue to leak outward.

Mitigation:

- Phase 40 should include minimal consumer alignment so external-facing consumers prefer `summary.decision_status`

## Recommendation

Proceed with Phase 40 now. The repo already has the artifact machinery and tests needed for this work. The correct move is to harden contract integrity at the producer seams before deterministic decision policy, calibration, and operator review layers are added on top.
