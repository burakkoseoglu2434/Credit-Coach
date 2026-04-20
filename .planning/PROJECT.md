# Project: Credit Coach

## Project Snapshot

Credit Coach is a trust-constrained decision intelligence and recourse system for denied or borderline lending customers. The product goal is to surface honest, operationally valid actions that improve customer outcomes without overstating certainty, violating planner constraints, or drifting away from the selected winner contract.

Current planning focus: **v2.7 Coverage Expansion & Action Surface Unlock**

Next planning command: `$gsd-plan-phase 71`

## What Has Been Proven

- **v2.5 Recoverable Customer Targeting & Movement Optimization** proved that recoverability signals, limited/full recourse routing, movement-focused ranking, and trust-safe narratives can be shipped without breaking validity guarantees.
- **v2.6 Real Cohort Evidence & Realization Proof** proved that the trust contract still holds on real cohort reruns and that evidence can be reported conservatively without causal overclaim.
- W2a evidence now makes the next bottleneck clear: the system is algorithmically capable, but the product surface is exposing only a narrow recoverable slice and is overusing empty-state limited mode.

## Active Milestone

### v2.7 Coverage Expansion & Action Surface Unlock

**Goal**

Expand actionable recommendation coverage beyond the current narrow recoverable slice and unlock multi-action, multi-step recommendation surfaces without breaking trust, validity, or consistency guarantees.

**Why This Milestone Exists**

- current actionable coverage is only about `~3%`
- about `~97%` of customers fall into empty-state limited mode
- surfaced recommendations are overly concentrated in a single action type
- the internal planner already generates richer multi-path strategies than the product surface exposes
- mid-risk and harder-denied customers currently receive little or no actionable progress guidance

**Success Criteria**

- actionable coverage increases from `~3%` to at least `10-20%`
- mid-risk customers receive non-zero actionable coverage
- surfaced recommendation mix contains multiple action types, with no single action type exceeding `50%` dominance
- multi-step or sequential plans are surfaced when they materially help the customer
- overall median `movement_score` remains above `0`
- trust counters remain clean:
  - `selected_invalid_winner_count = 0`
  - `selected_surface_drift_count = 0`
  - `operator_packet_contradiction_count = 0`

**Out Of Scope**

- model retraining
- threshold policy redesign
- new external data integrations
- new action types beyond already-supported semantics

## Planned Milestone Sequence

- **Phase 71: Coverage Diagnostics & Failure Analysis**
  - explain why customers fall into limited mode and quantify failure modes by segment
- **Phase 72: Recoverability Gate Relaxation (Controlled)**
  - introduce safer intermediate recoverability tiers and reduce empty-state overuse without breaking trust
- **Phase 73: Action Surface Expansion**
  - move from single-action surfacing to top-k action exposure using existing internal action diversity
- **Phase 74: Multi-Step Plan Surfacing**
  - turn flat outputs into sequential or staged plans where dependency-aware progression matters
- **Phase 75: Mid-Risk Segment Unlock**
  - surface longer-horizon or partial-progress plans for customers who are not immediately recoverable
- **Phase 76: Performance & Artifact Optimization**
  - keep larger-surface generation efficient and reproducible
- **Phase 77: Cohort Rerun & Comparative Evaluation**
  - validate coverage, movement, diversity, and trust outcomes against the W2a baseline

## Operating Constraints

- trust and winner-integrity contracts remain hard constraints, not soft objectives
- recommendation expansion must use existing model and action semantics
- new surfaced output must stay aligned with internal selected-path evidence
- milestone artifacts must remain reproducible and directly comparable to the W2a baseline
- evidence claims must remain descriptive and conservative

## Definition Of Done

- coverage and diversity improvements are validated through cohort reruns
- trust contracts remain fully preserved
- milestone artifacts are reproducible and comparable to W2a
- results are strong enough to support an investor narrative upgrade without overclaim
