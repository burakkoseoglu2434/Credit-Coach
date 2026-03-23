# Phase 43: Operator Review Pack - Research

**Researched:** 2026-03-23
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that turns the shipped decision and calibration artifacts into operator-usable review packets and a collection briefing, without creating a second decision system or leaking internal-only diagnostic states?

## Planning Basis

Phase 43 decisions were already discussed in-session and have been reconstructed into `43-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/43-operator-review-pack/43-CONTEXT.md`
- `credit-coach/src/credit_coach/coaching/messaging.py`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`
- `credit-coach/src/credit_coach/decision/ownership.py`
- `credit-coach/tests/test_messaging.py`
- `credit-coach/tests/test_customer_artifact_collection.py`

This is sufficient because the repo already has:

- null-free and parity-safe Phase 40 contracts
- one deterministic decision owner from Phase 40.5
- additive funnel, readiness, and calibration outputs from Phase 41
- messaging and schema seams that already separate business-safe narrative from technical detail

The gap is no longer missing decision truth. The gap is missing **operator packaging, queue prioritization, and review-speed-oriented rendering**.

## Executive Summary

Phase 43 should be planned as a **derived review-surface phase**, not as a decision or calibration phase.

The safest shape is:

`owned decision payload -> operator packet builder -> collection briefing builder -> additive packaging`

The code scan shows four important truths:

1. `messaging.py` already knows how to phrase decision, readiness, and offer truth in business-safe language
2. `schema.py` already supports the right pattern of short business-safe content plus technical appendix detail
3. `run_customer_artifact_collection.py` already owns the collection-root packaging seam where per-customer and collection-level operator artifacts should live
4. Phase 41 calibration artifacts already provide the review-priority signals Phase 43 needs, so Phase 43 does not need to create new ranking math

The clean split for this phase is therefore:

`per-customer packet contract -> collection-level briefing -> packaging and backward-compatible closure`

## Existing Assets We Can Reuse

### Messaging already owns business-safe phrasing

- `credit-coach/src/credit_coach/coaching/messaging.py`
  - already emits executive summary language
  - already speaks in decision-safe, readiness-aware, offer-aware product phrasing
  - already keeps technical reveal separate from the default summary layer

This is the right seam for:

- short packet phrasing
- normalized summary display
- business-safe downside and readiness language

### Typed schema already models short vs technical split

- `credit-coach/src/credit_coach/data/schema.py`
  - already holds typed narrative and technical-reveal structures
  - already mirrors the product principle that summary and appendix should coexist without mixing truth layers

This is the right seam for:

- typed operator packet payloads
- short-view and technical-appendix definitions
- packet-level field contract stability

### Collection runner already owns the packaging root

- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`
  - already writes per-customer raw outputs
  - already writes flat review outputs
  - already writes collection summary, manifest, and calibration subtree

This is the right seam for:

- per-customer operator packet artifacts
- collection-level operator briefing sections
- additive manifest and summary expansion

### Decision ownership already owns the truth

- `credit-coach/src/credit_coach/decision/ownership.py`
  - already returns the canonical decision payload
  - already owns `decision_reason_summary`, `decision_reason_drivers`, `expected_readiness`, subtype fields, confidence, and upgrade condition

This is the right truth source for:

- packet summary
- blocker derivation inputs
- offer-state and downside-risk interpretation

## Concrete Repo Findings

### 1. Operator-safe content ingredients already exist, but they are not packaged

The repo already has enough fields to answer:

- what is the decision?
- why is it not better?
- what changes the decision?
- when might it improve?
- what institution support exists?

But those truths still live across raw roadmap, flat tables, and calibration outputs rather than one operator-facing packet.

### 2. Collection summary is still analyst-rich but operator-light

Phase 41 added funnel and calibration packaging, but the summary is still oriented toward:

- cohort metrics
- calibration tables
- technical inspection

It does not yet answer the operator’s fast-review questions:

- who should I look at first?
- what blocker cluster dominates?
- which conditional subtype is the main queue?
- where does institution follow-up matter?

### 3. The correct abstraction is a derived packet, not a new truth source

Phase 40.5 and 41 already established:

- decision owner = shipped decision payload
- calibration = measurement layer

That means Phase 43 should not add a new decision object. It should add a **derived operator packet** and a **derived operator briefing** that stay tied to the existing truth owner.

### 4. `NEEDS_REVIEW` handling must stay diagnostic-only

Internal exception truth is still valuable for health and appendix use, but the Phase 43 packet must never surface it as a user-facing decision state. The correct place for it is:

- technical appendix
- collection health note
- optional debug signal

## What Phase 43 Must Deliver

### 1. Per-customer operator packet

Each customer should get a derived packet with:

- business-visible decision
- one-line reason
- blockers
- next best actions
- upgrade condition
- expected readiness
- offer state
- downside risk
- optional low-prominence confidence
- technical appendix reference

### 2. Collection-level operator briefing

Each collection run should gain a briefing that helps an operator decide:

- which queue to review first
- what blocker family dominates
- where conditional decisions concentrate
- which cases are likely to move soon
- where institution offer follow-up matters

### 3. Business-safe / technical split inside the same artifact

The safest packaging shape is:

- `short_view`
- `technical_appendix`

inside one packet artifact, rather than splitting truth across multiple independent packet families.

### 4. Additive packaging only

Phase 43 should add new artifacts and summary sections, but it should not break:

- raw customer artifacts
- flat review tables
- Phase 41 calibration artifacts
- existing collection-summary sections

## Recommended Plan Split

### Plan 43-01 — Per-customer operator packet contract and derivation

Focus on:

- typed packet schema
- summary passthrough guardrails
- blocker and action derivation
- readiness, upgrade path, offer state, and downside interpretation

### Plan 43-02 — Collection-level operator briefing and queue guidance

Focus on:

- funnel-to-queue translation
- blocker clustering
- conditional subtype hotspots
- likely-to-upgrade-soon queue
- gently directive review guidance

### Plan 43-03 — Packet packaging, markdown views, and backward-compatible closure

Focus on:

- packet artifact writes
- additive manifest and summary expansion
- same-run-root packaging
- technical appendix references and regression closure
