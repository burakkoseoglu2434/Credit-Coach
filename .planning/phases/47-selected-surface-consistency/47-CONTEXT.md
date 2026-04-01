# Phase 47 — Selected Surface Consistency Context

**Last updated:** 2026-04-01
**Status:** Discussed and locked
**Milestone:** `v2.2 Winner Integrity & Consumer Consistency`
**Requirements:** `CONS-01`, `CONS-02`, `CONS-03`

<domain>
## Phase Boundary

Phase 47 does **not** redesign:

- Phase 40.5 deterministic decision ownership semantics
- Phase 41 cohort / calibration math or reporting structure
- Phase 42 planner-quality or source-mix semantics
- Phase 42.5 recommendation validity taxonomy or warning posture
- Phase 43 operator packet semantics
- Phase 44 explanation-pack audience boundary or drift-guard posture
- Phase 45 winner hard-stop chooser contract
- Phase 46 DICE lane validity enforcement contract
- any threshold widening or approval-rate optimization

Phase 47 **does** own:

- making selected plan rows, external decision summaries, collection metrics, operator packets, and explanation packs speak about one coherent selected winner
- preventing external `CONDITIONAL` or `APPROVED` consumer surfaces from pointing at a raw selected plan row that leaks a contradictory technical `REJECTED` status
- defining a consumer-safe selected-surface overlay derived from the decision owner rather than exposing raw selected plan status directly
- making selected recommendation text come from one selected-plan projection owner instead of multiple surface-specific fallbacks
- defining an explicit empty-state contract for `no_valid_winner`
- adding a canonical drift-guard field set so selected-surface consistency is measurable in tests and reruns

Guardrails:

- external decision remains the consumer truth owner from Phase 40.5
- raw selected row may remain technical, but consumer surfaces may not read that raw status directly when it would contradict external decision truth
- Phase 47 fixes selected-surface coherence, not operator-packet blocker wording; packet coherence cleanup remains Phase 48 scope
- empty state must be explicit rather than hidden behind generic recommendation text

</domain>

<decisions>
## Implementation Decisions

### 1. Selected Row And External Decision Must Stay Coherent Through A Consumer-Safe Overlay

- Canonical rule:
  - external `decision_status` remains the consumer truth
  - selected row may keep the plan's technical status internally
  - but consumer surfaces may not expose a raw selected-row status that contradicts the external decision
- The system should therefore distinguish:
  - `selected_plan_status_internal` = technical selected-plan status
  - `selected_decision_status` = consumer-safe selected decision projection
- Hard consistency rule:
  - external `decision_status` and `selected_decision_status` must exact-match
- Prohibited leakage:
  - external `CONDITIONAL` with a consumer-visible selected `REJECTED` row
  - external `APPROVED` with a consumer-visible selected `REJECTED` row
- Raw plan rows may remain technical, but selected surfaces must consume the overlay rather than the raw technical status directly.

### 2. Selected Recommendation Text Has One Owner

- Canonical owner:
  - selected valid plan projection
- This owner should feed:
  - operator packet short-view recommendation
  - explanation pack recommended customer action
  - selected recommendation lines in any selected-surface summary
- Summary-level freeform fallback is **not** allowed just because a selected recommendation feels weak.
- Allowed fallback only:
  - explicit `no_valid_winner` empty state
  - or another explicit empty-state contract where no selected recommendation text should exist
- Canonical fields:
  - `selected_recommendation_text`
  - `selected_recommendation_source = selected_plan | empty_state`
- Hard rule:
  - operator packet and explanation pack may not generate different recommendation text if they are talking about the same selected truth.

### 3. `no_valid_winner` Must Be A True Empty State, Not A Fake Recommendation State

- `no_valid_winner` remains an explicit and null-safe selected-surface state.
- Minimum metrics / summary contract:
  - `best_plan_id = null`
  - `best_plan_source = null`
  - `best_action_count = 0`
  - `selection_outcome = no_valid_winner`
  - `selection_stage = no_valid_winner`
  - `plan_contract_pass = 0`
- Plan-table semantics:
  - all rows have `selected_best_flag = 0`
- Selected-surface input contract:
  - `selected_recommendation_text = null`
  - `selected_recommendation_source = empty_state`
  - `selected_action_count = 0`
- Consumer-output rule:
  - operator and explanation surfaces should render an explicit empty-state message such as:
    - `No valid recommendation path is currently available.`
  - they must not fabricate a generic behavioral recommendation to hide the empty state
- Canonical posture:
  - `no_valid_winner` is a real empty state, not a fake best plan.

### 4. Phase 47 Canonical Drift-Guard Field Set

- Hard identity fields that must exact-match across selected surfaces:
  - `best_plan_id`
  - `best_plan_source`
  - `selection_outcome`
  - `selection_stage`
- Consumer-truth fields that must exact-match across selected surfaces:
  - `decision_status`
  - `expected_readiness`
  - `selected_decision_status`
  - `selected_recommendation_text`
  - `selected_action_count`
- Optional-but-consistent fields may vary in wording, but must derive from the same payload:
  - driver text
  - blocker text
  - short summary wording
- Recommended first-class projection-trace field:
  - `selected_recommendation_projection_version`
- Purpose of the projection trace:
  - make it explicit that operator packet and explanation pack are consuming the same selected recommendation projection rather than recomputing it independently.

### Claude's Discretion

- Exact field names for technical-versus-consumer selected status, as long as the semantic split remains locked
- Whether `selected_recommendation_projection_version` is stored as a literal version string, hash-like token, or both
- Exact empty-state wording, as long as it remains explicit and does not masquerade as a real recommendation
- Whether selected-surface drift guards live in one helper or several focused assertions, as long as the locked field set is enforced

</decisions>

<specifics>
## Specific Ideas

- A selected raw row may remain technically `REJECTED`, but a consumer surface may never expose that raw technical status directly when the external decision is `CONDITIONAL`.
- Recommendation fallback freedom is the main enemy here; explicit empty-state is allowed, silent paraphrase drift is not.
- Phase 47 should make it obvious whether a surface is rendering:
  - selected-plan projection
  - explicit empty state
- `best_plan_id` consistency and recommendation-text consistency should be treated as the same chain, not separate concerns.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): builds roadmap summary, selection metadata, decision-owned summary, and narrative projection; currently the main seam where selected plan truth becomes selected-surface truth
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py): external decision owner; already separates technical plan signals from consumer-safe `decision_status` and `expected_readiness`
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): owns `selected_best_flag`, `best_plan_id` parity, and flat selected-row propagation
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py): derives short-view actions from roadmap narrative and currently falls back between `primary_recommendation` and `action_summary`
- [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py): already has drift guards for decision outcome, readiness, upgrade condition, and recommendation projection against operator packet

### Established Patterns
- Phase 40.5 external decision payload remains the business-safe consumer truth.
- Phase 44 already established that operator packet and explanation pack are shared-truth, different-audience consumers.
- Phase 45 already made `no_valid_winner` an explicit selection outcome rather than a corruption signal.
- Phase 46 already proved that selected DICE winners are eligibility-clean; Phase 47 therefore focuses on selected-surface coherence, not contender validity.

### Integration Points
- `run_recourse.py` needs a first-class selected-surface overlay instead of letting raw selected plan status leak into downstream surfaces
- `run_customer_artifact_collection.py` needs selected-row / selected-decision parity checks that understand the new overlay contract
- `operator_review.py` and `decision_explanation_pack.py` should consume the same selected recommendation projection
- tests should cover external `CONDITIONAL` versus technical selected-plan `REJECTED` drift explicitly

</code_context>

<deferred>
## Deferred Ideas

- Contradictory approved fallback blockers remain Phase 48 scope.
- Operator short-view blocker wording and packet tone cleanup remain Phase 48 scope.
- Threshold widening, approval uplift, and broader consumer-channel expansion remain out of scope.

</deferred>

---

*Phase: 47-selected-surface-consistency*
*Context gathered: 2026-04-01*
