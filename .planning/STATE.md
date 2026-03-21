# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-20)

**Core value:** Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints, then surface those plans in a form that enterprise buyers and analysts can trust.
**Current focus:** `v2.0 Personalized Action & Decision Intelligence`

## Current Position

Phase: 32
Plan: research complete, plans written
Status: Ready for execution
Last activity: 2026-03-21 - Planned Phase 32 around verdict normalization, repair-vs-reject hardening, and feasibility visibility alignment

Progress: `v2.0` is underway; Phases 30-31 are complete and the next active design seam is Phase 32 feasibility and constraint hardening

## Performance Metrics

**Velocity:**
- Total plans completed: 81 (historical import + phases 8-25 plus phases 30-31)
- Average duration: historical data not reconstructed
- Total execution time: historical data not reconstructed

**By Milestone:**

| Milestone | Plans | Total | Avg/Plan |
|-----------|-------|-------|----------|
| v1.0 historical baseline | 20 | historical import | n/a |
| v1.1 completed milestone | 12 | phases 8-11 complete | n/a |
| v1.2 completed milestone | 15 | phases 12-16 complete | n/a |
| v1.3 completed milestone | 28 | phases 17-25 complete | n/a |
| v2.0 active milestone | 6 | phases 30-31 complete, phases 32-39 remaining | n/a |

**Recent Trend:**
- The engine now has audited full-portfolio proof plus buyer-safe demo, proof, investor, analyst, and pilot-baseline surfaces.
- The new milestone is focused on making outputs more customer-specific, numeric, decision-intelligent, and easier to validate at portfolio scale.
- The roadmap now continues from Phase 32 with the next sequence covering feasibility, execution realism, offers, narratives, surfaces, portfolio impact, calibration, and pilot integration.

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- `v1.2 Recommendation Quality Hardening` remains the shipped recommendation-quality baseline
- `v1.3 Portfolio Intelligence & Productization` treated the website as milestone scope rather than side documentation
- Phase 17 anchored product claims to full-portfolio evidence and demo representativeness
- Phase 18 moved buyer and analyst narrative translation into the engine-owned contract
- Phase 19 and Phase 20 re-hardened execution-aware ranking and deterministic trajectory behavior
- Phase 21 shipped product-facing proof verdicts and the curated `product_confidence_snapshot.json`
- Phase 22 and Phase 23 turned Demo, Proof, and Investor into business-first surfaces with technical detail on demand
- Phase 24 closed analyst validation through one matrix, one walkthrough packet, and one milestone-local results artifact
- Phase 25 closed pilot-readiness baseline through structured intake, explicit ops docs, and a curated demo handoff playbook
- Milestone audit: `v1.3 Portfolio Intelligence & Productization` passed with 9/9 requirements satisfied, 7/7 integrations, and 6/6 end-to-end flows
- Milestone archive: `v1.3` roadmap and requirements are now snapshotted under `.planning/milestones/`, and active planning files have been reset for the next milestone boundary
- Milestone open: `v2.0 Personalized Action & Decision Intelligence` is now the active planning target
- v2.0 initialization intentionally skipped separate research because the milestone goal was already explicit and grounded in fresh brownfield milestone history
- The milestone was then replanned around a longer `Phase 30-39` sequence to reflect the user's desired build order
- Phase 30 execution is complete and establishes:
  - final top-level taxonomy `behavioral | structural | institutional`
  - canonical `action_family`
  - one primary action per actionable feature
  - deterministic grouped-action semantics
  - schema-level `business_view` vs `technical_view`
- Phase 30 also aligns roadmap, messaging, and batch consumers to grouped semantic actions rather than raw feature-first defaults
- The next active design seam is `Phase 31: Numeric Target Engine`
- Phase 31 context now locks:
  - minimum-credible-change posture
  - one canonical point target per action
  - absolute target plus signed delta
  - `action_family`-first unit selection with controlled overrides
  - one primary numeric target for mixed-unit actions
  - semantic-sanity-only generation guardrails before Phase 32 feasibility
- Phase 31 planning is now split into:
  - numeric target contract and unit catalog
  - generator integration and feasibility handoff
  - runtime consumer alignment and regression closure
- Phase 31 execution is complete and establishes:
  - one canonical `PrimaryNumericTarget` per action
  - deterministic `action_family`-driven metric and unit selection
  - generator-emitted numeric targets with feasibility-neutral handoff notes
  - runtime and messaging consumers that prefer primary numeric targets over raw feature deltas
  - grouped-step narrative selection that prefers the step carrying the primary numeric target
- `NUM-01` is now satisfied
- The next active design seam is `Phase 32: Feasibility & Constraint Engine`
- Phase 32 context now locks:
  - canonical action-level verdicts `valid | clipped | repaired | provisional | invalid`
  - worst-dominant plan-level verdict precedence `invalid > provisional > repaired > valid`
  - canonical `constraint_family` layer
  - `repair-if-safe, reject-if-semantic-break`
  - business default shows only feasibility outcome labels while raw trace stays technical-only
- Phase 32 planning is now split into:
  - verdict and constraint-family normalization
  - repair-vs-reject and ranking-safe rollups
  - business-vs-technical visibility and consumer alignment

### Pending Todos

None yet.

### Blockers/Concerns

- The local `gsd-tools.cjs` helper is missing internal modules, so milestone-op automation and some workflow helpers still require manual fallback.
- The website build still emits the existing Vite chunk-size warning for the main bundle, though it remained non-blocking for `v1.3`.
- Unrelated local work outside `.planning` still exists in the repo and should stay isolated from next-milestone setup.

## Session Continuity

Last session: 2026-03-21
Stopped at: Phase 32 planning complete; next step is `$gsd-execute-phase 32`
Resume file: None
