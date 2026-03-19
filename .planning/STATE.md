# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-17)

**Core value:** Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints, then surface those plans in a form that enterprise buyers and analysts can trust.
**Current focus:** `v1.3 Portfolio Intelligence & Productization`

## Current Position

Phase: 20
Plan: Not planned
Status: Ready for discussion
Last activity: 2026-03-19 - Completed Phase 19 with conservative execution truth, stronger execution-aware ranking, and risk-band-centered behavior evidence

Progress: Phases 17-19 complete; Phase 20 still pending discussion and planning

## Performance Metrics

**Velocity:**
- Total plans completed: 47 (historical import + phases 8-16)
- Average duration: historical data not reconstructed
- Total execution time: historical data not reconstructed

**By Milestone:**

| Milestone | Plans | Total | Status |
|-----------|-------|-------|--------|
| v1.0 historical baseline | 20 | historical import | Complete |
| v1.1 completed milestone | 12 | phases 8-11 complete | Complete |
| v1.2 completed milestone | 15 | phases 12-16 complete | Complete |
| v1.3 active milestone | 9 complete | phases 17-19 complete, Phase 20 pending discussion | Open |

**Recent Trend:**
- The recourse engine is already typed-action-aware, behavior-aware, trajectory-aware, offer-aware, and learning-capable.
- Full-portfolio proof now exists, including product-ready coverage, reality-gap audit, and demo representativeness diagnostics.
- The engine now emits buyer- and analyst-ready roadmap narratives directly, including executive summary, checkpoint meaning, reasons, and technical reveal.
- Behavior-aware recourse has now been re-hardened with conservative execution truth, stronger planner demotion, and nominal-vs-execution-aware executive evidence.
- The post-18 roadmap has been partially rebuilt: Phase 19 reopens behavior-aware recourse hardening and Phase 20 reopens sequential trajectory hardening inside `v1.3`.
- Future work after Phase 20 remains intentionally open until the next redesign pass.

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- `v1.2 Recommendation Quality Hardening` remains the shipped baseline for typed actions, behavior-aware ranking, trajectories, offers, and learning evidence
- The next milestone is `v1.3 Portfolio Intelligence & Productization`
- Phase numbering continues from 17 rather than restarting around website work
- Full-portfolio evaluation is now the first planned phase because demo and proof claims must be grounded in whole-cohort evidence
- `credit-coach-website/` is now treated as milestone scope, not side documentation
- The Python engine remains source-of-truth and website surfaces should consume curated artifact-derived snapshots rather than reimplement model logic
- Business-first analyst and buyer language is now an explicit milestone requirement rather than an implied polishing task
- Phase 17 shipped a canonical portfolio proof seam under `portfolio_validation.py` and batch/suite artifact emission
- Phase 17 locked and implemented:
  - `raw / valid / governance-safe / product-ready` coverage as the canonical funnel
  - reality-gap as audit-first and non-blocking
  - derived `recoverability_segment` and `offer_needed_segment`
  - canonical demo verdicts: `representative | optimistic | narrow | misleading`
  - suite-level supporting and release artifact references for portfolio proof
- Phase 18 discussion locked:
  - engine-side canonical narrative contract
  - `customer_roadmap.narrative` as sibling translated layer
  - executive summary by default and `technical_reveal` on demand
  - one shared UI-ready schema for website and analyst views
  - template-driven, deterministic, controlled-vocabulary narration
- Phase 18 shipped:
  - engine-owned roadmap narrative schema and serialization
  - deterministic action, checkpoint, offer, and reason narration
  - confidence labels plus controlled technical reveal
  - website typed mirror that consumes engine narrative instead of inventing story text
- On 2026-03-19, all planned phases after 18 were intentionally removed from the roadmap so the remaining `v1.3` sequence could be redesigned from a clean state
- On 2026-03-19, `Phase 19: Behavior-Aware Recourse` and `Phase 20: Sequential / Trajectory Planning` were added back as explicit hardening passes over inherited `v1.2` capability
- On 2026-03-19, Phase 19 discussion locked:
  - balanced but mildly conservative execution-probability posture
  - strong execution-aware ranking demotion
  - weighted min-average composite aggregation
  - dual realization layers for executable vs approval-dependent branches
  - nominal-vs-execution-aware comparison as the executive evidence center
- On 2026-03-19, Phase 19 planning split the work into:
  - estimator and realization hardening
  - ranking leverage and provisional contender behavior
  - artifact, suite, and review emphasis
- On 2026-03-19, Phase 19 shipped:
  - conservative execution-probability posture with burden+horizon hardening
  - dual executable vs approval-dependent realization truth
  - stronger execution-aware winner selection and provisional demotion
  - risk-band-centered nominal-vs-execution-aware behavior proof

### Roadmap Evolution

- Phase 19 added: Behavior-Aware Recourse
- Phase 20 added: Sequential / Trajectory Planning

### Pending Todos

None yet.

### Blockers/Concerns

- The local `gsd-tools.cjs` helper is still missing internal modules, so some GSD workflow helpers remain manual
- The website exists as a brownfield surface with live and curated demo seams, but its proof language is still ahead of full-portfolio validation
- Some recent website demo work is still uncommitted outside `.planning`; milestone-definition work should avoid mixing with those unrelated edits

## Session Continuity

Last session: 2026-03-19
Stopped at: Phase 19 complete; next step is to run `$gsd-discuss-phase 20` or `$gsd-plan-phase 20 --research`
Resume file: None
