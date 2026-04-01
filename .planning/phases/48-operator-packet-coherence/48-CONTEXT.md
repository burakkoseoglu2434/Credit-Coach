# Phase 48 — Operator Packet Coherence Context

**Last updated:** 2026-04-01
**Status:** Discussed and locked
**Milestone:** `v2.2 Winner Integrity & Consumer Consistency`
**Requirements:** `OPER-01`, `OPER-02`, `OPER-03`

<domain>
## Phase Boundary

Phase 48 does **not** redesign:

- Phase 40.5 deterministic decision ownership semantics
- Phase 41 calibration or readiness math
- Phase 42 planner-quality or source-mix semantics
- Phase 42.5 recommendation validity taxonomy or warning posture
- Phase 45 winner hard-stop logic
- Phase 46 DICE contender enforcement
- Phase 47 selected projection contract or empty-state identity
- threshold widening or approval-rate optimization

Phase 48 **does** own:

- making operator packet short view internally coherent for `APPROVED`, `CONDITIONAL`, `REJECTED`, and `no_valid_winner` states
- ensuring blockers, next actions, readiness, upgrade path, and recommendation text never contradict the selected consumer truth already established in Phase 47
- suppressing incoherent fallback blockers instead of fabricating packet guidance
- defining packet-specific render modes, diagnostics, and aggregate coherence metrics so operator contradictions are measurable in tests and reruns

Guardrails:

- selected truth still comes from the Phase 47 selected projection; Phase 48 may suppress or reinterpret packet rendering, but it does not invent a new selected truth owner
- explanation pack remains a separate artifact; this phase is about operator packet coherence, not explanation-pack redesign
- DICE cleanliness and winner integrity remain inherited and fixed baselines; this phase assumes they are already true
- empty-state packets must stay explicit and must not hide behind generic behavioral coaching text

## Problem Statement

After Phase 47, selected truth is aligned across raw summary, flat metrics, operator packet, and explanation pack. The remaining trust gap is **operator packet coherence**:

- approved packets can still show fallback blockers even when there are no active decision drivers
- blocker / next action / readiness combinations can still tell mixed stories inside the same packet
- short-view guidance can still over-render packet content that should be suppressed for the current decision state

The goal of Phase 48 is therefore not to change decision ownership or selected truth, but to make the operator packet a **coherent consumer** of that truth.

</domain>

<decisions>
## Implementation Decisions

### 1. Status-Specific Operator Packet Contract

Operator packet rendering must be decision-state aware.

#### `APPROVED` packets

- `top_blockers` must be empty
- `next_best_actions` must be empty
- fallback blocker rendering is forbidden
- `upgrade_condition` should be suppressed in short view
- readiness is informational only, never blocker-like
- approved packets may carry technical appendix detail, but the short view may not imply that approval is still blocked

#### `CONDITIONAL` packets

- packet must render at least one meaningful blocker or one meaningful next action
- if `selected_recommendation_source = selected_plan` and `selected_action_count > 0`, the first short-view action must come from the selected projection
- blockers may come from structured drivers or a status-compatible primary-reason fallback
- readiness is allowed, but must be rendered in a way consistent with the condition:
  - `unknown_review` -> manual-review interpretation
  - time-based readiness -> time-gated interpretation
- `upgrade_condition` may remain visible

#### `REJECTED` packets

- blockers may render
- next actions are allowed only when the selected projection is a real selected-plan recommendation
- if there is no selected-plan recommendation, packet must not fabricate one
- readiness may only be rendered as `not_ready` or manual-review style context, never as near-term approval language
- `upgrade_condition` may remain visible if it reflects the decision-owned summary

#### `no_valid_winner` packets

- packet is a real empty state
- `next_best_actions` must be empty
- `selected_recommendation_source` must remain `empty_state`
- generic recommendation text is forbidden
- blockers may render only from real decision drivers or from one explicit empty-state blocker
- readiness may render only as context, never as a disguised recommendation

### 2. Blocker Rendering Rules

- primary blocker owner remains `decision_reason_drivers`
- blocker fallback must be **status-aware**
- allowed fallback sources:
  - `APPROVED` -> none
  - `CONDITIONAL` -> only a compatible primary reason (`LOW_EXECUTION`, `OFFER_BLOCK`, `TIME_BLOCK`, `DATA_ISSUE`)
  - `REJECTED` -> only a compatible primary reason (`NO_PATH`, `LOW_IMPACT`, `LOW_EXECUTION`)
  - `no_valid_winner` -> one explicit empty-state blocker when no drivers exist
- incompatible fallback blockers must be suppressed rather than rendered

### 3. Next Action Rendering Rules

- the first short-view action is owned by the selected projection from Phase 47
- short view may not invent a new recommendation when selected projection is empty
- institution conditions may supplement a customer action, but may not stand alone as a customer action row
- supplementary actions from narrative steps are allowed only when they:
  - do not duplicate the selected projection
  - do not contradict the packet decision state
  - relate to at least one rendered blocker or the same selected improvement path

### 4. Readiness Interpretation Rules

- readiness is packet context, not an alternate blocker system
- `APPROVED`:
  - readiness is informational only
  - packet must not use readiness to imply that approval is still blocked
- `CONDITIONAL`:
  - `unknown_review` must render as manual-review context, not as time-to-approval
  - time-based readiness may render only if it matches the decision-owned conditional posture
- `REJECTED`:
  - readiness must not read like a near-term upgrade promise
  - `not_ready` or manual-review framing only
- `no_valid_winner`:
  - readiness may appear as context but cannot be paired with fake next actions

### 5. Recommendation Text Versus Blocker Consistency

- if actions are rendered and blockers are rendered, the first action must address at least one rendered blocker
- if blockers are suppressed, action rendering must record that suppression explicitly in packet diagnostics
- packet may not show:
  - an approved decision with a blocker
  - an empty-state packet with a next action
  - an institution-only condition pretending to be a customer action

### 6. Packet Coherence Diagnostics Are First-Class

Phase 48 should add packet-specific diagnostics instead of silently improvising:

- `active_driver_count`
- `blocker_render_source = driver | primary_reason | empty_state | suppressed`
- `action_render_source = selected_projection | empty_state | suppressed`
- `readiness_render_mode = approved_info | conditional_time_gate | conditional_manual_review | rejected_not_ready | rejected_manual_review | empty_state_context | suppressed`
- `fallback_blocker_suppressed`
- `packet_coherence_codes`

These are packet-debug and rerun-proof fields, not new business-facing states.

## Required Artifact / Schema Changes

### Schema

Additive packet fields should live in `OperatorPacketTechnicalAppendix`, and when helpful in `OperatorPacketShortView`:

- `active_driver_count: int`
- `blocker_render_source: str | None`
- `action_render_source: str | None`
- `readiness_render_mode: str | None`
- `fallback_blocker_suppressed: bool`
- `packet_coherence_codes: list[str]`

### Flat / Collection Surfaces

Additive flat metrics fields:

- `operator_blocker_render_source`
- `operator_action_render_source`
- `operator_readiness_render_mode`
- `operator_packet_coherence_codes_json`
- `operator_fallback_blocker_suppressed`

Additive collection summary lenses:

- `approved_with_blocker_count`
- `approved_with_action_count`
- `approved_with_upgrade_condition_count`
- `empty_state_with_action_count`
- `action_blocker_mismatch_count`
- `readiness_decision_mismatch_count`
- `fallback_blocker_suppressed_count`

## Acceptance Criteria

Phase 48 exits only when all of the following are true:

1. `0` approved packets render any blocker
2. `0` approved packets render any next-best action
3. `0` approved packets render a short-view upgrade condition
4. `0` empty-state packets render a next-best action
5. `0` empty-state packets masquerade as `selected_plan` recommendation source
6. `0` packets render a first action that mismatches all rendered blockers
7. `0` packets render a readiness interpretation incompatible with the packet decision state
8. warning badges and appendix diagnostics remain available without contradicting the short view

Large-sample proof remains required on:

- `pilot_mixed`
- `risk_band_balanced`
- `offer_needed_balanced`

## Outputs / Artifacts

Phase 48 should produce:

- coherent `operator_packet.json`
- coherent `operator_packet.md`
- additive packet coherence fields in flat customer metrics
- collection summary / manifest evidence for operator packet coherence
- targeted regression tests covering all four decision / empty-state modes

## Recommended Implementation Order

1. **Status-aware render contract**
   - make blocker, action, readiness, and upgrade rendering decision-state aware in `operator_review.py`
2. **Coherence diagnostics and schema propagation**
   - add packet render-source / coherence fields to schema, flat metrics, and collection summary
3. **Regression closure and rerun proof**
   - add targeted unit and integration tests, then prove the contract on the three 250-customer cohorts

### Claude's Discretion

- Exact coherence-code names, as long as they cleanly separate blocker, action, readiness, and empty-state contradictions
- Whether `upgrade_condition` suppression is represented as `null`, `""`, or a dedicated render-mode path, as long as approved packets do not show it in short view
- Whether readiness render modes are stored as literals or compact enums, as long as the semantic split above remains fixed

</decisions>

<specifics>
## Specific Ideas

- The root Phase 48 bug seam is `_fallback_blocker(...)` in [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py): approved packets currently inherit a blocker when drivers are empty.
- The first action should stay projection-owned, but operator packet is allowed to suppress it for `APPROVED` or `empty_state` packets.
- Readiness note text must be render-mode-aware instead of blindly reusing the same helper for every decision state.
- Packet appendix should become the first-class debug surface for “why this packet rendered this way.”

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py): owns short-view blockers, actions, readiness, markdown rendering, and packet metrics; this is the main Phase 48 seam
- [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py): already drift-checks decision and selected recommendation projection, so it provides a useful reference for packet truth ownership even though Phase 48 should not redesign it
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py): decision owner for `decision_status`, `decision_reason_drivers`, `upgrade_condition`, and `expected_readiness`
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py): packet schemas already have a technical appendix and can take additive coherence fields cleanly
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): already propagates operator packet metrics into flat outputs and collection summary, so it is the natural proof surface for Phase 48 aggregates

### Established Patterns

- Phase 45 already made selected winner integrity explicit and safe.
- Phase 46 already ensures DICE winners are contender-clean before selection.
- Phase 47 already established one selected projection owner and an explicit empty-state packet identity.
- Therefore Phase 48 should focus only on how the operator packet **renders** and **suppresses** short-view elements, not on how selected truth is decided.

### Integration Points

- `_blockers_from_summary(...)` and `_fallback_blocker(...)` need decision-state-aware suppression
- `_actions_from_narrative(...)` needs packet-mode-aware action suppression and coherence checks
- `build_operator_review_packet(...)` needs status-specific short-view assembly
- `render_operator_review_packet_markdown(...)` must honor the same suppressions as JSON output
- operator packet metrics and collection summary need coherence counters that make regressions visible in reruns

</code_context>

<deferred>
## Deferred Ideas

- any change to decision ownership or readiness calculation itself
- any change to selected projection ownership or explanation-pack audience semantics
- any threshold widening or approval-rate optimization
- broader borrower-facing surface cleanup beyond operator packet coherence

</deferred>

---

*Phase: 48-operator-packet-coherence*
*Context gathered: 2026-04-01*
