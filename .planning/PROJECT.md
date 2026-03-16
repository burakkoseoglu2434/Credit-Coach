# Credit Coach

## What This Is

Credit Coach is a credit-risk and recourse platform that moves beyond binary approve/deny decisions. It predicts probability of default, explains model behavior, and generates feasible action plans that can help denied customers reach approval while staying within fairness, reliability, latency, and governance gates.

The project serves two connected goals: an academically credible research core and a production-oriented fintech productization path. After shipping `v1.2`, the system now has a stronger recommendation-quality core and is ready for the next milestone definition rather than more unscoped build-out.

## Core Value

Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints.

## Current State

`v1.2 Recommendation Quality Hardening` shipped on `2026-03-16` and passed milestone audit. Credit Coach now supports:
- typed behavioral, structural, and institutional actions
- behavior-aware execution probability and expected-utility ranking
- phased trajectories with checkpoint and replan metadata
- institution-side offer optimization under inherited governance gates
- compact learning-ledger logging, normalized delayed outcomes, and confidence-aware offline policy evaluation

The active planning state is now a milestone boundary rather than an open execution phase.

## Next Milestone Goals

No new milestone is open yet. The next step is to define it explicitly with `$gsd-new-milestone`.

Near-term candidate directions already visible in the repo:
- operator-facing productization and dashboard surfaces
- richer regulatory explanation and adverse-action narratives
- recurring automation around release review and milestone health

<details>
<summary>Archived Milestone Context: v1.2 Recommendation Quality Hardening</summary>

**Goal:** Improve the real-world validity, feasibility, and behavioral realism of recourse recommendations by expanding action semantics, modeling action execution probability, enabling sequential trajectory planning, integrating institutional offer optimization, and strengthening outcome feedback loops.

**Target features:**
- Real-world action taxonomy spanning behavioral, structural, and institutional actions
- Stronger feasibility, dependency, and conflict constraints for financially realistic plans
- Behavior-aware execution probability and expected-utility scoring
- Sequential multi-phase trajectory planning with partial-execution simulation
- Offer optimization and learning loops that connect recommendation quality to real outcomes

</details>

## Requirements

### Validated

- ✓ Core PD modeling, calibration, and deterministic backend controls exist in the codebase - v1.0
- ✓ Gate-aligned recourse generation, feasibility controls, and high-risk or trajectory flows exist in the codebase - v1.0
- ✓ Fairness, stress, benchmark, challenger, telemetry, and release-gate workflows exist in the codebase - v1.0
- ✓ Seeded fairness, KPI contract, candidate-quality, telemetry evidence, and outcome-feedback packaging are hardened - v1.1
- ✓ Recommendation quality is now typed-action-aware, behavior-aware, trajectory-aware, offer-aware, and learning-loop-capable - v1.2

### Active

- [ ] Define the next milestone and its requirement contract with `$gsd-new-milestone`
- [ ] Choose which carried-forward productization and automation goals should become active next-milestone scope

### Out of Scope

- Major new end-user product surfaces - planning remains focused on the core recommendation engine until a future milestone explicitly broadens borrower-facing UX
- New domain pivots outside credit recourse - the roadmap remains tightly centered on credit approval improvement
- Legal or compliance opinion automation - the work continues to define engineering controls, not legal advice
- Fully online autonomous learning or policy deployment - outcome learning remains evidence-first before any production auto-promotion

## Context

- The repository already contains a substantial brownfield implementation under `credit-coach/`.
- The imported `v1.0` baseline established model, recourse, fairness, telemetry, and audit foundations.
- `v1.1 Fairness Stability & KPI Hardening` remains the audited governance baseline.
- `v1.2 Recommendation Quality Hardening` is now shipped and audited, adding typed actions, execution-aware ranking, trajectories, offer optimization, and learning-loop evidence.
- Existing batch, suite, challenger, telemetry, and outcome-feedback seams are now richer and should still be reused rather than replaced in the next milestone.
- No next milestone has been locked yet, so planning should reopen with explicit scope definition instead of drifting into unsourced build work.

## Constraints

- **Governance**: Fairness, reliability, telemetry, and release gates remain inherited constraints; recommendation realism cannot override them
- **Behavioral Realism**: New actions must model actual customer or institution behavior, not just favorable feature edits
- **Reproducibility**: New scoring, simulation, and learning loops must remain testable and artifact-driven
- **Operational Safety**: Outcome feedback and offer optimization may add business value, but must stay auditable and degradation-aware
- **Brownfield**: Existing implementation patterns, artifacts, and runner seams must be respected - this is not a greenfield reset
- **Milestone Continuity**: Phase numbering continues from imported v1.0 and completed v1.1 or v1.2 history - the next milestone should continue from Phase 17

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use GSD `.planning` as the single planning home for this repo | Legacy docs were scattered across repo root and `credit-coach/docs`, making continuity and phase tracking difficult | ✓ Good |
| Preserve legacy source documents under `.planning/` instead of discarding them | The old files contain historical context, evidence, and implementation detail needed for audits and future planning | ✓ Good |
| Treat the repository as a brownfield GSD project | Existing code and reports prove the project is already in active development | ✓ Good |
| Reconstruct phases 1-7 as historical `v1.0` baseline work | This preserves continuity while allowing milestone-based planning to start cleanly at Phase 8 | ✓ Good |
| Treat `v1.1 Fairness Stability & KPI Hardening` as the audited hardening baseline | Fairness, KPI, telemetry, and release evidence contracts are now stable enough to support deeper recommendation work | ✓ Good |
| Open `v1.2 Recommendation Quality Hardening` as the active milestone | The next meaningful upgrade is moving from a gate-aware recourse engine toward a behavior-aware sequential recourse decision engine | ✓ Good |
| Treat `v1.2 Recommendation Quality Hardening` as shipped and archived before opening new work | Typed actions, behavior-aware ranking, trajectories, offers, and learning evidence are now in place, so the next step should be a fresh milestone contract | ✓ Good |

---
*Last updated: 2026-03-16 after completing and archiving milestone v1.2*
