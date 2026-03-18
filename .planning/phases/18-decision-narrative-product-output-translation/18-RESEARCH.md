# Phase 18: Decision Narrative & Product Output Translation - Research

**Researched:** 2026-03-18
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so Credit Coach can translate engine-native recommendation output into deterministic, business-first narratives that enterprise buyers and analysts can trust, while preserving raw truth, technical traceability, and a single engine-owned source contract?

## Planning Basis

Phase 18 now has a locked `18-CONTEXT.md`. For this planning pass, the authoritative sources are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/18-decision-narrative-product-output-translation/18-CONTEXT.md`
- `.planning/phases/17-full-portfolio-evaluation-coverage-audit/17-CONTEXT.md`
- `.planning/phases/14-sequential-recourse-planning/14-CONTEXT.md`
- `.planning/phases/15-policy-optimization-layer/15-CONTEXT.md`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/coaching/messaging.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/policy/engine.py`
- `credit-coach/tests/test_messaging.py`
- `credit-coach/tests/test_policy_engine.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach-website/shared/demo-schema.ts`
- `credit-coach-website/server/services/live-demo.ts`
- `credit-coach-website/client/src/lib/demo-formatters.ts`
- `credit-coach-website/client/src/pages/DemoCenterPage.tsx`

This is sufficient because the phase boundary is no longer about recommendation quality itself. That truth is already locked by earlier phases. The remaining work is to build one controlled translation layer on top of that truth and prove that website and analyst surfaces can consume it without inventing their own interpretation logic.

## Executive Summary

The repository already contains the ingredients for Phase 18, but they are split across engine and website seams:

- `schema.py` already carries typed actions, trajectory phases, and trajectory checkpoints
- `run_recourse.py` already emits the canonical `customer_roadmap.json`
- `messaging.py` already translates adverse-action drivers into human-readable reason payloads
- the website already has executive-summary and controlled-reveal UX patterns
- `live-demo.ts` currently performs an important but overly thick translation step from raw output to product language

That means Phase 18 should not invent a new product layer outside the engine. It should:

1. extend engine-owned artifact truth with a canonical `narrative` branch
2. standardize step, checkpoint, offer, and reason narration through deterministic templates
3. add a controlled `technical_reveal` seam rather than deleting technical depth
4. make website and analyst surfaces consume the same schema at different visibility levels

The main risk of the phase is drift:

- if website keeps translating on its own, demo and analyst views will diverge
- if translation becomes too freeform, product trust will drop
- if translation hides too much, analysts lose traceability
- if translation exposes too much, buyers see engine-native output instead of product value

The locked context resolves that risk by choosing a clear contract:

- engine-side narrative schema is the source of truth
- `customer_roadmap.narrative` is the sibling translated layer
- default output is business-first
- technical truth remains available via `technical_reveal`
- deterministic templates and controlled vocabulary are mandatory

## Existing Assets We Can Reuse

### Engine-owned action and trajectory truth already exists

- `credit-coach/src/credit_coach/data/schema.py`
  - `PlanAction` already carries action title, action class, offer metadata, diagnostic flags, and execution probability
  - `TrajectoryPhase` and `TrajectoryCheckpoint` already carry the plan’s time structure

This means Phase 18 does not need a second recommendation model. It only needs a narrative-bearing projection of existing plan truth.

### The customer roadmap serialization seam already exists

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `_build_customer_roadmap(...)` already serializes:
    - phases
    - step details
    - checkpoints
    - plan status
    - trajectory metadata

This is the natural place to attach one canonical `narrative` branch without splitting source-of-truth across multiple artifacts.

### Adverse-action translation already has a foundation

- `credit-coach/src/credit_coach/coaching/messaging.py`
  - already exposes:
    - `build_adverse_action_reasons`
    - `build_adverse_action_payload`
  - already maps risk factors to:
    - title
    - description
    - remediation hint

Phase 18 should reuse and extend this seam rather than inventing a separate reason-language layer.

### Website already demonstrates the desired UX pattern

- `credit-coach-website/client/src/pages/DemoCenterPage.tsx`
  - already shows executive summary first
  - already uses controlled reveal for deeper details
- `credit-coach-website/server/services/live-demo.ts`
  - already performs product-oriented interpretation of raw engine output

This is useful evidence, but it also shows the current architectural problem:

- the website is doing too much of the translation

Phase 18 should move canonical translation upstream into the engine so website becomes a thin consumer.

## What Phase 18 Must Deliver

Phase 18 should be planned around three concrete outcomes:

### 1. One canonical narrative contract

The engine must emit a sibling narrative layer such as:

- `customer_roadmap.narrative.executive_summary`
- `customer_roadmap.narrative.steps`
- `customer_roadmap.narrative.checkpoints`
- `customer_roadmap.narrative.technical_reveal`

The contract must be machine-readable and deterministic.

### 2. One controlled translation system

Every plan should be able to express:

- what to do
- why it matters
- what outcome is expected
- what happens if the step succeeds
- what happens if it does not

This applies not only to ordinary actions, but also to:

- offers
- checkpoints
- principal risk reasons

### 3. One shared schema for website and analyst surfaces

The website and analyst views should not have different data contracts.

They should render the same artifact with different visibility levels:

- website:
  - executive summary
  - clean step narratives
  - checkpoint stories
  - limited offer detail
- analyst:
  - full narrative
  - technical reveal
  - confidence details
  - diagnostic flags

## Recommended Implementation Split

The roadmap’s three planned Phase 18 plans are the right split.

### Plan 18-01 — Narrative contract and action template library

This should do the core engine work:

- add narrative-bearing schema fields
- define deterministic narrative object shape
- create action template library
- create plan-level executive summary contract
- attach step-level narratives to serialized roadmap output

This is the phase’s backbone because the rest depends on one stable narrative shape.

### Plan 18-02 — Technical reveal, reasons, offers, checkpoints, and confidence

This should deepen the same narrative system:

- controlled `technical_reveal`
- checkpoint narrative fields
- offer narrative sub-blocks
- adverse-action sentence translation
- confidence labeling
- vocabulary consistency rules

This is where the product avoids the false tradeoff between “clean” and “traceable.”

### Plan 18-03 — UI-ready schema validation across surfaces

This should prove that the narrative contract is really usable:

- align website consumer schema to engine output
- thin `live-demo.ts` and related website translation seams
- validate same artifact can feed website and analyst views
- keep default rendering business-first
- keep technical reveal accessible without UI-side inference

This is the phase’s trust test: “engine says it, product says it.”

## Main Planning Constraints

### Do not create a second truth contract

The phase must not leave website as a competing semantic layer. Website mirrors are allowed; website-owned logic is not.

### Do not introduce freeform copy generation

The user explicitly wants:

- template-driven language
- controlled vocabulary
- deterministic fills

So the plan should not depend on LLM-generated explanation text.

### Do not weaken technical traceability

Phase 18 is not a marketing rewrite. Technical truth must remain present through `technical_reveal`.

### Do not reopen earlier modeling phases

The narrative layer can describe:

- trajectories
- offers
- execution likelihood
- reasons

But it must not redefine:

- the planner
- ranking rules
- portfolio proof logic
- offer math
- learning-loop math

## Validation Implications

Phase 18 needs both engine-side and website-side regression proof.

The most important new checks are:

### Engine-side

- schema-level narrative contract tests
- `customer_roadmap.json` serialization tests
- deterministic template behavior tests
- reason translation tests
- confidence label mapping tests

### Website-side

- shared schema compatibility checks
- TypeScript typecheck
- production build
- demo consumer compatibility without UI-side inference

The likely new or expanded test seams are:

- `credit-coach/tests/test_messaging.py`
- `credit-coach/tests/test_policy_engine.py`
- `credit-coach/tests/test_recourse_redesign.py`
- a new dedicated narrative-contract test file
- `credit-coach-website` `npm run check`
- `credit-coach-website` `npm run build`

## Risks To Watch During Execution

### 1. Website drift risk

If Phase 18 only adds fields but leaves website translation logic mostly intact, the milestone will look complete but still drift over time.

### 2. Overly thin narrative risk

If the narrative contract contains only superficial summaries, analysts will still need raw engine output to understand a plan.

### 3. Overly rich schema risk

If the contract becomes too broad or repetitive, the website may keep ad hoc formatting logic anyway.

### 4. Bilingual inconsistency risk

Because the website is bilingual, Phase 18 should plan for consistency-friendly tokenization and controlled vocabulary, not only English-first copy.

## Recommended Success Frame

At the end of Phase 18, the project should be able to say:

> The engine now emits one deterministic narrative contract that explains what the customer should do, why it matters, what to expect at checkpoints, and which technical drivers sit underneath the story. Website and analyst surfaces both consume that same artifact without inventing their own interpretation layer.

That is the right interpretation of `PORT-02`.
