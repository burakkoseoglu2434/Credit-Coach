# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-15)

**Core value:** Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints.
**Current focus:** Phase 16 is now replanned under locked context and the next work is executing the learning-ledger logging, completeness tiers, and proxy-vector OPE contracts

## Current Position

Phase: 16 of 16 (Outcome Feedback & Learning Loop)
Plan: 0 of 3 in current phase
Status: Planned
Last activity: 2026-03-16 - Replanned Phase 16 against the locked learning-ledger, completeness-tier, proxy-vector OPE, and Learning Loop Summary contracts

Progress: [########--] 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 44 (historical import + phases 8-15)
- Average duration: historical data not reconstructed
- Total execution time: historical data not reconstructed

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| v1.0 historical baseline | 20 | historical import | n/a |
| v1.1 completed milestone | 12 | phases 8-11 complete | n/a |
| v1.2 active milestone | 12 | phases 12-15 complete, phase 16 pending | n/a |

**Recent Trend:**
- Last 5 plans: historical data not reconstructed
- Trend: Offer optimization is now first-class, so the roadmap can finish the learning loop on top of typed actions, behavior-aware ranking, trajectories, and offer-policy evidence

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Migration: Legacy root/docs material is now stored under `.planning/`
- Migration: Historical plans and reports remain preserved as source evidence
- Milestone: Imported phases 1-7 are treated as historical `v1.0` baseline work
- Milestone: Current work starts at Phase 8 under `v1.1 Fairness Stability & KPI Hardening`
- Phase 8: Shared seeded fairness release semantics now drive suite, smoke, and challenger behavior
- Phase 9 context: canonical runner contract is `kpi_contract_snapshot.json`, explicit freeze is fail-closed, degraded evidence is never acceptance-eligible, and milestone acceptance is derived from repeated seeded evidence
- Phase 9 complete: smoke, suite, and challenger now emit or consume canonical KPI contract snapshots and milestone acceptance artifacts
- Phase 10 context: canonical candidate-quality fields are diversity, entropy, and `best_source_*_rate` over the `denied` population, with `high_risk_denied` as companion evidence
- Phase 10 context: high-risk tuning is promotion evidence only, uses `denied_high_risk_lift` as the primary success metric, and requires `high_risk_profile_applied_rate >= 0.05` to count as non-anecdotal
- Phase 10 complete: candidate-quality evidence is now canonical in batch, suite, and challenger artifacts under the locked source taxonomy
- Phase 11 complete: telemetry is now a fail-closed operational prerequisite in smoke while preserving the underlying release-decision contract
- Phase 11 complete: the suite emits canonical `release_evidence_pack.json`, and challenger or smoke emit compatible local evidence snapshots
- Phase 11 complete: outcome-feedback artifacts now publish machine-readable control-relative proxy summaries and feed the Phase 11 review surface
- Milestone audit: `v1.1 Fairness Stability & KPI Hardening` passed with 12/12 requirements satisfied and no phase or flow gaps
- Milestone archive: active `v1.1` roadmap and requirements are snapshotted under `.planning/milestones/`
- Milestone open: `v1.2 Recommendation Quality Hardening` is now active with phases 12-16 covering action realism, behavior-aware recourse, sequential planning, offer optimization, and learning loops
- Inheritance: `v1.2` explicitly carries forward fairness, reliability, telemetry, and machine-readable evidence contracts from `v1.1`
- Phase 12 complete: typed action taxonomy now uses a hybrid action unit where `action_key` is user-facing and `feature_name` remains the effect anchor
- Phase 12 complete: feasibility realism now emits reason-coded clip or reject outcomes, including semantic rejection when clipping destroys the action intent
- Phase 12 complete: dependency, conflict, and approval-required behavior now flow through one machine-readable constraint layer with `valid | repaired | provisional | invalid` plan states
- Phase 12 complete: batch evaluation now emits canonical `action_realism_summary.json` plus breakdown artifacts for action types, feasibility rejections, repairs, and approval-pending actions
- Phase 13 planned: execution probability will extend the typed-action and serialized-plan contracts rather than creating a second planner stack
- Phase 13 planned: expected utility and partial-execution evidence will remain subordinate to inherited fairness, reliability, telemetry, and acceptance gates
- Phase 13 context locked: canonical probability units are action- and plan-level, composite actions aggregate through `action_group_id`, and approval-dependent actions remain non-winner evidence
- Phase 13 context locked: weekly coaching loop is the canonical partial-execution seam and `behavior_aware_summary.json` is the mandatory non-blocking supporting artifact
- Phase 13 replanned: research and execution prompts now explicitly inherit the locked probability, expected-utility, simulation, and artifact decisions
- Phase 13 complete: generated actions and plans now carry explicit execution-likelihood metadata through a shared `execution_probability.py` seam
- Phase 13 complete: planner ranking now uses expected PD improvement as a behavior-aware ordering signal only after inherited constraint and governance gates
- Phase 13 complete: batch, suite, challenger, and milestone review artifacts now expose canonical behavior-aware summaries and partial-execution evidence without redefining acceptance gates
- Phase 14 planned: canonical trajectory structure should build on existing `phase_id`, `time_months`, checkpoint, and roadmap seams rather than replacing them
- Phase 14 planned: the weekly coaching loop remains the dynamic simulation grain for checkpoint and partial-execution trajectory behavior
- Phase 14 planned: phase-aware optimization must remain subordinate to inherited fairness, reliability, telemetry, and acceptance gates
- Phase 14 context locked: `phases[]` is the canonical trajectory semantic layer, the phase set is fixed, and one action belongs to one primary phase
- Phase 14 context locked: checkpoint policy is `4w > 12w > 24w` with soft monotonicity expectations and review-boundary replan behavior
- Phase 14 replanned: execution prompts now inherit hybrid trajectory transitions, short-term-first optimization, conservative high-risk policy, and trajectory policy labels
- Phase 14 complete: plans now expose canonical `phases[]`, checkpoint metadata, and review-boundary trajectory state under one shared `trajectory.py` seam
- Phase 14 complete: weekly-loop simulation now drives trajectory checkpoint evidence, soft regression penalties, and machine-readable transition breakdowns
- Phase 14 complete: planner, suite, challenger, and review surfaces now share phase-aware optimization evidence and policy labels without weakening inherited governance gates
- Phase 15 context locked: offer-bearing actions remain institutional actions with an added `offer_type` and `offer_terms` layer rather than a second planner stack
- Phase 15 context locked: recovery optimization uses `expected_recovery_proxy` over `approval_rate`, `default_rate_90d`, and `avg_margin_90d`, but only after inherited gates and short-term trajectory health
- Phase 15 context locked: `offer_acceptance_probability` stays distinct from `plan_execution_probability`, with `combined_plan_realization_probability` used only for offer-bearing plans
- Phase 15 context locked: `offer_optimization_summary.json` will be mandatory supporting evidence, non-blocking, and explanation-first in review
- Phase 15 planned: offer-bearing institutional actions will become explicit mixed-plan primitives with structured terms and one active offer branch at most
- Phase 15 planned: recovery-aware ranking will remain governance-first and use separate offer-acceptance plus combined-realization semantics
- Phase 15 planned: suite, challenger, outcome feedback, and milestone review will all consume one canonical `offer_optimization_summary.json` evidence contract
- Phase 15 complete: institution-side offers now appear as explicit term-bearing institutional actions under the existing typed-action stack, with one active rankable offer branch at most
- Phase 15 complete: planner and batch evaluation now use distinct offer-acceptance plus combined-realization semantics and publish canonical `offer_optimization_summary.json` evidence
- Phase 15 complete: suite, challenger, outcome feedback, and milestone review now consume offer-policy evidence under one seeded supporting contract with explanation-first review output
- Phase 16 planned: decision logging will expand to carry recommendation, offer, execution, propensity, and candidate-set context keyed by `decision_id`
- Phase 16 planned: outcome feedback will normalize action completion, offer acceptance, payment, default, and recovery signals into learning-ready artifacts with explicit completeness status
- Phase 16 planned: the repo will add IPS and Doubly Robust off-policy evaluation as supporting learning evidence rather than as a new release gate
- Phase 16 context locked: decision logging is a compact learning ledger with `selection_propensity` plus `propensity_source`, not a duplicated full plan snapshot
- Phase 16 context locked: completeness is graded as `descriptive_only | partial_learning_ready | learning_ready`, with explicit coverage dimensions and a primary 90-day learning window
- Phase 16 context locked: OPE remains proxy-vector-first, control-baselined, confidence-aware, and non-blocking, and review gains a separate `Learning Loop Summary`
- Phase 16 replanned: research and execution prompts now explicitly inherit the compact learning-ledger contract, completeness tiers, 90-day readiness window, and separate learning review surface

### Pending Todos

None yet.

### Blockers/Concerns

- The local `gsd-tools.cjs` helper is missing internal modules, so GSD document commits and some workflow helpers must be handled manually for now.
- Historical `v1.0` execution was reconstructed from imported docs rather than phase-by-phase GSD summaries, so plan-level metrics are approximate.

## Session Continuity

Last session: 2026-03-16 19:48
Stopped at: Phase 16 replanned; next step is `$gsd-execute-phase 16`
Resume file: None
