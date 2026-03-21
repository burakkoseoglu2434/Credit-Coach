# Phase 35: Narrative Generation v2 - Research

**Researched:** 2026-03-22
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so Credit Coach can turn hardened semantic, numeric, feasibility, execution, and offer truth into personalized, product-ready narratives that stay business-first by default, technically complete on demand, and deterministic enough to remain engine-owned?

## Planning Basis

Phase 35 now has a locked `35-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/18-decision-narrative-product-output-translation/18-CONTEXT.md`
- `.planning/phases/30-action-semantics-hardening/30-CONTEXT.md`
- `.planning/phases/31-numeric-target-engine/31-CONTEXT.md`
- `.planning/phases/32-feasibility-constraint-engine/32-CONTEXT.md`
- `.planning/phases/33-action-difficulty-execution-modeling/33-CONTEXT.md`
- `.planning/phases/34-offer-layer-integration/34-CONTEXT.md`
- `.planning/phases/35-narrative-generation-v2/35-CONTEXT.md`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/coaching/messaging.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/tests/test_messaging.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach/tests/test_portfolio_validation.py`

This is sufficient because Phase 35 is not inventing a new narrative system from scratch. The repo already contains:

- an engine-owned narrative branch under `customer_roadmap`
- step, checkpoint, offer, reason, and technical reveal schemas
- numeric target wording
- feasibility, difficulty, readiness, and confidence labels
- offer-specific companion narrative blocks

The gap is no longer whether narrative output exists. The gap is whether that output is personalized enough, granular enough, and disciplined enough to carry the new v2.0 truth stack without drifting into either raw engine dump or hype-driven product copy.

## Executive Summary

Phase 18 created the first engine-owned narrative layer. Phases 30 through 34 then hardened:

- semantic action identity
- customer-specific numeric targets
- feasibility truth
- difficulty and follow-through truth
- explicit offer contracts

Phase 35 must now re-harden narrative so those newer truths are expressed cleanly and coherently.

The codebase already behaves as if Narrative Generation v2 is partially present:

- `schema.py` already carries `RoadmapExecutiveSummary`, `RoadmapStepNarrative`, `OfferNarrative`, `RoadmapCheckpointNarrative`, `RoadmapReasonNarrative`, and `RoadmapTechnicalReveal`
- `messaging.py` already generates deterministic wording for steps, reasons, checkpoints, follow-through, and offers
- primary numeric targets already appear in step-level wording
- runtime already serializes the narrative branch as part of `customer_roadmap`

What is still missing is one locked contract for:

1. narrative granularity and ordering
2. personalization posture
3. business vs technical visibility boundaries for narrative truth
4. tone and persuasion discipline

Phase 35 should therefore be planned as:

`narrative contract/order hardening -> personalization and tone hardening -> business-vs-technical narrative split and runtime closure`

## Existing Assets We Can Reuse

### The engine-owned narrative schema already exists

- `credit-coach/src/credit_coach/data/schema.py`
  - already contains the full narrative object family:
    - `RoadmapExecutiveSummary`
    - `RoadmapStepNarrative`
    - `OfferNarrative`
    - `RoadmapCheckpointNarrative`
    - `RoadmapReasonNarrative`
    - `RoadmapTechnicalReveal`
    - `CustomerRoadmapNarrative`
  - is the correct seam for tightening field expectations rather than building a parallel contract

### The narrative builder already exists

- `credit-coach/src/credit_coach/coaching/messaging.py`
  - already builds:
    - executive summary
    - step narratives
    - checkpoint narratives
    - reason narratives
    - offer narratives
    - technical reveal payloads
  - already formats:
    - primary numeric target statements
    - feasibility labels
    - difficulty labels
    - follow-through notes
    - readiness cards
    - confidence labels
  - is the primary implementation seam for Phase 35

### Runtime artifact ownership is already solved

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - already emits `customer_roadmap.narrative`
  - is the right place to preserve engine-owned truth while narrative wording is upgraded

This means Phase 35 can stay entirely engine-first and does not need to move into the website layer yet. Product-surface consumption remains Phase 36.

## What Phase 35 Must Deliver

### 1. Narrative granularity that matches the hardened truth stack

Phase 35 must lock:

- default order:
  - `executive_summary`
  - `steps`
  - `checkpoints`
  - `reasons`
- one clear action meaning per step
- one primary numeric statement per step
- compact feasibility and difficulty cues on each visible step
- all three checkpoints visible, with `4w` dominant and `12w/24w` supporting

### 2. Personalization that comes from truth, not persona copy

Phase 35 must make personalization feel grounded in:

- current state
- target
- timing
- behavior signal
- offer support when present

It must avoid:

- explicit segment jargon in default copy
- judgmental tone
- persona-writing that is detached from numeric or behavioral truth

### 3. Business-safe default narrative and technical-complete reveal

Phase 35 must keep default output lean:

- no raw probabilities
- no dense secondary metrics
- only top `2-3` reasons

While still keeping technical reveal complete enough to explain how the story was formed:

- primary numeric target
- feasibility trace
- difficulty drivers
- offer contract
- plan realization probabilities

### 4. Tone discipline

Phase 35 must keep narrative:

- calm
- confident
- non-judgmental
- gently directive
- honest but non-threatening
- deterministic first, expressive second

This is the main trust guardrail that keeps v2.0 from sounding like AI-generated coaching copy.

## Recommended Plan Split

### Plan 35-01 — Narrative contract and ordering hardening

Focus on:

- tightening step and checkpoint narrative contract behavior
- keeping `action_summary` semantically clean
- putting the primary numeric target into `expected_outcome`
- ensuring every visible step carries short feasibility, difficulty, and follow-through cues
- preserving full `4w / 12w / 24w` visibility with explicit `4w` emphasis

### Plan 35-02 — Personalization and tone hardening

Focus on:

- current-state, target, and timing-led personalization
- behavior-led but non-judgmental wording
- customer-path-first offer-bearing narratives
- top `2-3` reason curation for default story layers
- calm, confident, gently directive negative and positive outcome phrasing

### Plan 35-03 — Business-vs-technical split and runtime closure

Focus on:

- enforcing one primary numeric statement per step in default narrative
- keeping secondary metrics and raw probabilities in technical reveal only
- widening technical reveal to carry the minimum narrative-generation truth set
- protecting runtime serialization and downstream artifact stability
- closing regression coverage around deterministic narrative output

## Main Risks

### Risk 1: Narrative becomes denser without becoming clearer

If Phase 35 adds more truth but not more structure, the result will be a bigger artifact rather than a better product narrative.

Mitigation:

- lock ordering
- keep one primary numeric statement per step
- keep `4w` emphasis explicit

### Risk 2: Personalization drifts into artificial copy

If the system tries to sound personal without grounding itself in current state, target, and timing, the copy will feel synthetic.

Mitigation:

- derive personalization from hardened truth only
- keep segment language implicit rather than explicit

### Risk 3: Business and technical layers blur again

If raw probabilities or secondary metrics leak into the default story, product readability will drop.

Mitigation:

- enforce business-safe defaults
- push full trace into `technical_reveal`

### Risk 4: Tone becomes either too weak or too pushy

If wording stays too descriptive, the product will not guide action. If it becomes too motivational, trust will drop.

Mitigation:

- lock the tone as calm, confident, gently directive, and non-threatening
- keep deterministic templates rather than freeform expressive generation

## Recommendation

Proceed with Phase 35 now. The engine already owns the narrative surface; the next step is to make that surface worthy of the v2.0 truth stack by tightening granularity, personalization, split boundaries, and tone before Phase 36 begins rendering richer product experiences on top of it.
