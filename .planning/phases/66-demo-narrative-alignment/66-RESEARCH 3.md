# Phase 66: Demo & Narrative Alignment - Research

**Researched:** 2026-04-10
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest deterministic producer + consumer alignment that makes recoverable vs limited-mode outcomes obvious in the demo story, without changing planner/threshold/action semantics and without introducing drift between customer surfaces, operator packets, explanation packs, and website demo rendering?

## Planning Basis

Phase 66 decisions are locked in:

- `.planning/phases/66-demo-narrative-alignment/66-CONTEXT.md`

Authoritative project context:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`

## Executive Summary

Phase 66 should be planned as a **contract alignment pass** across:

1) **Python producer surfaces** (`customer_roadmap.json` summary + narrative, operator packet, explanation pack)
2) **Website demo consumer** (schema + server normalization + Demo Center page)

The main technical risk is **copy drift caused by timing/order of attachments**:

- `run_recourse.py` builds `roadmap["narrative"]` **before** recoverability signal + recourse gate are applied (gate is attached later in the bundle path).
- `_apply_recourse_gate_to_roadmap(...)` can clear narrative steps in limited mode, but it does not currently ensure the *executive summary* reads informational rather than actionable.

Planning implication:
- Align narrative posture by making narrative generation **aware of** the shipped gate truth (`recourse_mode`, `recommendation_mode`, `recoverable_flag`, `recoverability_bucket`, blockers).
- Ensure website demo stops synthesizing meaning (fallback action mapping, computed readiness stage, default step details) and renders engine-owned fields or explicit “Unavailable” placeholders.

## Concrete Repo Findings

### 1) Shipped truth is already present in the engine, but not elevated into a stable narrative contract

Producer truth exists and is deterministic:
- `credit-coach/src/credit_coach/evaluation/recoverability.py`
  - `build_recoverability_signal(...)` emits `approval_gap`, `recoverability_bucket`, blocker lists/flags, and reason codes.
  - `build_recoverability_classifier(...)` emits `recoverable_flag` and `recoverable_reason_codes`.
  - `build_recourse_gate(...)` emits `recourse_mode`, `recommendation_mode`, and gate version/reason codes.
- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `_attach_recoverability_signal_to_roadmap(...)` attaches signal + classifier truth into `roadmap["summary"]`
  - `_apply_recourse_gate_to_roadmap(...)` attaches gate truth and enforces limited-mode empty-state selected projection

Gap for Phase 66:
- `narrative_type` (`actionable|informational`) and `informational_subtype` are not emitted as stable fields.
- The executive narrative copy can read like “a recovery path is in place” even when the gate forces limited/informational posture.

### 2) The narrative layer is centralized and is the right place for deterministic wording templates

- `credit-coach/src/credit_coach/coaching/messaging.py`
  - `build_customer_roadmap_narrative(...)` builds executive summary cards + reasons + technical reveal.

Planning implication:
- Introduce deterministic templates keyed by `narrative_type` and `informational_subtype`.
- Keep customer-facing text short and safe; keep operator-facing details in operator packet / technical appendix.

### 3) Operator and explanation artifacts already enforce “external-safe” contracts; Phase 66 should extend them additively

- `credit-coach/src/credit_coach/ops/operator_review.py` builds the operator packet from `roadmap["summary"]` + narrative steps.
- `credit-coach/src/credit_coach/ops/decision_explanation_pack.py` builds an external-safe pack and enforces drift checks (covered by tests).
- Existing tests:
  - `credit-coach/tests/test_operator_packet_coherence.py`
  - `credit-coach/tests/test_decision_explanation_pack.py`

Planning implication:
- Add posture fields (`narrative_type`, `informational_subtype`, `recourse_mode`, etc.) additively to packet/pack surfaces.
- Keep `NEEDS_REVIEW` and raw traces out of external surfaces (unchanged guardrail).

### 4) Website live demo currently “fills in” missing meaning — Phase 66 must remove this inference

- `credit-coach-website/server/services/live-demo.ts` currently:
  - computes readiness stage from checkpoints
  - synthesizes `detail` text via `ACTION_DETAILS`
  - synthesizes action meta via `FEATURE_ACTIONS`
  - generates fallback step IDs when missing
  - enforces `REQUIRED_DECISION_STATUS = "APPROVED"` (in tension with v2.5 denied targeting narrative)

Planning implication:
- Treat the website as a typed consumer:
  - pass through engine-provided posture fields and narrative text
  - downgrade missing fields to explicit “Unavailable in this view” placeholders rather than synthesizing content
  - support two deterministic demo cases (actionable vs informational) without changing engine truth

## Recommended Plan Shape

1. **66-01 (Wave 1): Engine narrative contract**
   - Emit `narrative_type`, `informational_subtype`, and `narrative_contract_version` deterministically in `customer_roadmap.json`.
   - Ensure limited-mode executive narrative is informational and explicitly states “no plan promoted”.
   - Add focused pytest coverage for mapping + copy safety.

2. **66-02 (Wave 2): Operator + explanation alignment**
   - Add posture fields to operator packet + explanation pack (additive).
   - Ensure drift checks remain intact and tests prove external-safe posture coherence.

3. **66-03 (Wave 3): Website demo consumption**
   - Update shared demo schema to include posture fields and allow optionality where engine truth is absent.
   - Remove `ACTION_DETAILS` / `FEATURE_ACTIONS` inference and stop recomputing readiness stage.
   - Allow two demo cases (actionable/informational) and remove the `APPROVED` hard requirement.
   - Validate via `npm run check` + `npm run build`.

## Validation Architecture

Use existing guardrails:
- Python: `tests/test_messaging.py`, `tests/test_operator_packet_coherence.py`, `tests/test_decision_explanation_pack.py`, `tests/test_selected_surface_consistency.py`
- Website: `cd credit-coach-website && npm run check && npm run build`

