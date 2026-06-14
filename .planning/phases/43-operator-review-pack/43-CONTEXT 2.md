# Phase 43 — Operator Review Pack Context

**Last updated:** 2026-03-23
**Status:** Discussed and locked
**Milestone:** `v2.1 Decision Ownership & Pilot-Ready Trust`
**Requirements:** `OPS-01`, `OPS-02`

## Phase Boundary

Phase 43 does **not** redesign:

- Phase 40 contract normalization or raw-flat parity rules
- Phase 40.5 deterministic decision ownership or policy logic
- Phase 41 cohort semantics, funnel math, or shadow calibration math

Phase 43 **does** own:

- operator-facing per-customer packet structure
- collection-level operator briefing structure
- business-readable review UX over the existing decision payload
- the split between short operator-safe review and technical appendix detail

Guardrails:

- business-facing outputs remain `APPROVED | CONDITIONAL | REJECTED`
- `NEEDS_REVIEW` stays internal-only and exception-only
- operator packets must consume existing Phase 40.5 decision payload and Phase 41 calibration artifacts
- operator packets and briefings must not create new decision truth

## Exact Goal

Turn customer and collection outputs into a reviewable, partner-ready operator workflow package that supports 50-customer review in under 30 minutes.

## Area 1 — Per-Customer Operator Packet Contract

### Locked Decisions

1. Packet format is `short + expanded`
2. Packet is a separate derived artifact:
   - `operator_packet.json`
   - preferably `operator_packet.md`
3. Canonical packet order:
   - `decision_header`
   - `1-line summary`
   - `blockers`
   - `next best actions`
   - `upgrade path`
   - `readiness`
   - `offer state`
   - `downside risk`
   - `technical appendix`
4. Minimum required blocks:
   - `decision_status`
   - `decision_reason_summary`
   - `top_blockers`
   - `next_best_actions`
   - `expected_readiness`
   - `upgrade_condition`
   - `offer_state`
   - `downside_risk`
   - `technical_detail_available`
5. Packet should also carry:
   - `decision_confidence`
   - `conditional_type`
   - `rejection_type`

### Guardrails

- raw truth owner remains `customer_roadmap.json`
- operator surface is a derived view only
- operator packet must not compute decisions, readiness, or calibration locally

## Area 2 — Explanation, Blockers, And Next Actions

### Locked Decisions

1. `1-line summary` source of truth is directly `decision_reason_summary`
2. Messaging may only do:
   - phrasing normalization
   - truncation
   - display cleanup
3. Raw structured drivers stay in the packet
4. Short layer shows top `2-3` drivers as numeric, target-oriented business-readable lines
5. `top_blockers` explain why the customer is not in a better state today
6. `next_best_actions` are the most concrete `1-3` responses to those blockers
7. Every `next_best_action` must trace to at least one blocker
8. `upgrade_condition` and `expected_readiness` stay separate:
   - `upgrade_condition` = what changes the decision upward
   - `expected_readiness` = when the customer would likely become approval-ready if that change occurs

### Display Rules

- short-layer drivers should prefer numeric language over generic labels
- blockers explain the present limitation
- actions explain the next move
- packet cannot invent a new summary line if `decision_reason_summary` already exists

## Area 3 — Collection-Level Operator Briefing

### Locked Decisions

1. Canonical section order:
   - `decision funnel`
   - `priority queues`
   - `dominant blockers`
   - `conditional hotspots`
   - `offer hotspots`
   - `review guidance`
   - `technical appendix refs`
2. Required operator-safe aggregate surfaces:
   - approved / conditional / rejected counts
   - highest-volume blocker groups
   - top conditional subtypes
   - expected readiness distribution
   - offer-needed concentration
   - `likely_to_upgrade_soon`
3. Calibration inputs promoted into operator-safe summary:
   - `approved_share`
   - `conditional_share`
   - `rejected_share`
   - `approve_plus_conditional_share`
   - readiness headline
   - dominant segment hotspots
4. `internal_needs_review_share` may appear only as a small health note
5. Technical appendix references may include:
   - raw `decision_shift_matrix`
   - full `segment_breakdown`
   - full candidate policy tables
6. Tone should be `gently directive`

### Guardrails

- briefing may guide prioritization, but must not become an automated playbook
- operator summary may consume calibration outputs, but must not become a tuning dashboard

## Area 4 — Business-Safe vs Technical-Detail Split

### Locked Decisions

1. Default business-safe layer shows:
   - `decision_status`
   - `1-line summary`
   - top `2-3` blockers
   - top `1-3` next actions
   - `upgrade_condition`
   - `expected_readiness`
   - `offer_state`
   - `downside_risk`
   - optional low-prominence `decision_confidence`
2. Technical detail stays in the same artifact as:
   - `short_view`
   - `technical_appendix`
3. `NEEDS_REVIEW` must never appear as a user-facing decision state
4. `NEEDS_REVIEW` may appear only as:
   - diagnostic appendix signal
   - small debug badge
   - collection health note
5. `offer_state` should use product language:
   - `kurum teklifi aktif`
   - `kurum teklifine bağlı`
   - `müşteri kabulüne bağlı`
   - `kurum teklifi yok`
6. `downside_risk` should be honest but non-threatening

### Internal Standardization Notes

- downside risk may internally map to:
  - `time_risk`
  - `approval_risk`
  - `execution_risk`
- short layer should still show one soft sentence rather than exposing raw internal labels

## Likely Code Seams

- `credit-coach/src/credit_coach/coaching/messaging.py`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`
- `credit-coach/src/credit_coach/decision/ownership.py`
- `credit-coach/tests/test_messaging.py`
- `credit-coach/tests/test_customer_artifact_collection.py`

## Phase-Local Success Definition

Phase 43 is successful when:

- each customer run can emit one operator-safe packet without inventing new truth
- collection outputs include an operator briefing that prioritizes review work clearly
- `NEEDS_REVIEW` remains internal and diagnostic-only
- operator surfaces remain business-readable while preserving appendix-level traceability
