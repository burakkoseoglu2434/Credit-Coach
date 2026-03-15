# Credit Coach

## What This Is

Credit Coach is a credit-risk and recourse platform that moves beyond binary approve/deny decisions. It predicts probability of default, explains model behavior, and generates feasible action plans that can help denied customers reach approval while staying within fairness, reliability, latency, and governance gates.

The project serves two connected goals: an academically credible research core and a production-oriented fintech productization path. The current milestone focuses on improving the behavioral realism, feasibility, and learning value of the recourse engine now that `v1.1` has stabilized the measurement and release-governance backbone.

## Core Value

Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints.

## Current Milestone: v1.2 Recommendation Quality Hardening

**Goal:** Improve the real-world validity, feasibility, and behavioral realism of recourse recommendations by expanding action semantics, modeling action execution probability, enabling sequential trajectory planning, integrating institutional offer optimization, and strengthening outcome feedback loops.

**Target features:**
- Real-world action taxonomy spanning behavioral, structural, and institutional actions
- Stronger feasibility, dependency, and conflict constraints for financially realistic plans
- Behavior-aware execution probability and expected-utility scoring
- Sequential multi-phase trajectory planning with partial-execution simulation
- Offer optimization and learning loops that connect recommendation quality to real outcomes

## Requirements

### Validated

- ✓ Core PD modeling, calibration, and deterministic backend controls exist in the codebase - v1.0
- ✓ Gate-aligned recourse generation, feasibility controls, and high-risk or trajectory flows exist in the codebase - v1.0
- ✓ Fairness, stress, benchmark, challenger, telemetry, and release-gate workflows exist in the codebase - v1.0
- ✓ Seeded fairness, KPI contract, candidate-quality, telemetry evidence, and outcome-feedback packaging are hardened - v1.1

### Active

- [ ] Expand the action space beyond feature edits into behavioral, structural, and institutional recommendation types
- [ ] Strengthen feasibility realism so recommendations respect monthly, income, utilization, and institutional constraints
- [ ] Incorporate execution probability and partial-execution behavior into recommendation scoring
- [ ] Move from one-shot plans to multi-phase trajectories that balance short-term feasibility with long-term risk improvement
- [ ] Integrate institution-side offers and outcome-learning loops without weakening fairness, reliability, or telemetry safeguards

### Out of Scope

- Major new end-user product surfaces - this milestone remains focused on the core recommendation engine rather than borrower-facing UX
- New domain pivots outside credit recourse - the roadmap remains tightly centered on credit approval improvement
- Legal or compliance opinion automation - the work continues to define engineering controls, not legal advice
- Fully online autonomous learning or policy deployment - outcome learning remains evidence-first before any production auto-promotion

## Context

- The repository already contains a substantial brownfield implementation under `credit-coach/`.
- The imported `v1.0` baseline established model, recourse, fairness, telemetry, and audit foundations.
- `v1.1 Fairness Stability & KPI Hardening` is complete, audited, and now serves as the stable governance baseline for future recommendation work.
- The dominant blocker has shifted from release-contract instability to recommendation realism: richer action semantics, stronger feasibility, execution likelihood, sequential planning, and institutional optimization.
- Existing batch, suite, challenger, telemetry, and outcome-feedback seams should be reused where possible so new recommendation-quality evidence inherits the same machine-readable release discipline.
- The user provided the initial `v1.2` milestone scope directly in GSD-ready form, so this milestone launch starts from a locked milestone contract rather than open-ended discovery.

## Constraints

- **Governance**: Fairness, reliability, telemetry, and release gates remain inherited constraints; recommendation realism cannot override them
- **Behavioral Realism**: New actions must model actual customer or institution behavior, not just favorable feature edits
- **Reproducibility**: New scoring, simulation, and learning loops must remain testable and artifact-driven
- **Operational Safety**: Outcome feedback and offer optimization may add business value, but must stay auditable and degradation-aware
- **Brownfield**: Existing implementation patterns, artifacts, and runner seams must be respected - this is not a greenfield reset
- **Milestone Continuity**: Phase numbering continues from imported v1.0 and completed v1.1 history - current work starts at Phase 12

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use GSD `.planning` as the single planning home for this repo | Legacy docs were scattered across repo root and `credit-coach/docs`, making continuity and phase tracking difficult | ✓ Good |
| Preserve legacy source documents under `.planning/` instead of discarding them | The old files contain historical context, evidence, and implementation detail needed for audits and future planning | ✓ Good |
| Treat the repository as a brownfield GSD project | Existing code and reports prove the project is already in active development | ✓ Good |
| Reconstruct phases 1-7 as historical `v1.0` baseline work | This preserves continuity while allowing milestone-based planning to start cleanly at Phase 8 | ✓ Good |
| Treat `v1.1 Fairness Stability & KPI Hardening` as the audited hardening baseline | Fairness, KPI, telemetry, and release evidence contracts are now stable enough to support deeper recommendation work | ✓ Good |
| Open `v1.2 Recommendation Quality Hardening` as the active milestone | The next meaningful upgrade is moving from a gate-aware recourse engine toward a behavior-aware sequential recourse decision engine | ✓ Good |

---
*Last updated: 2026-03-15 after starting milestone v1.2*
