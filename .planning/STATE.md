# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-17)

**Core value:** Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints, then surface those plans in a form that enterprise buyers and analysts can trust.
**Current focus:** `v1.3 Portfolio Intelligence & Productization`

## Current Position

Phase: 18
Plan: 3 planned
Status: Ready for execution
Last activity: 2026-03-18 - Planned Phase 18 with narrative contract, controlled technical reveal, and shared UI-ready schema workstreams

Progress: ready for `$gsd-discuss-phase 18` or `$gsd-plan-phase 18 --research`

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
| v1.3 active milestone | 6 | phase 17 complete, phase 18 next | Open |

**Recent Trend:**
- The recourse engine is already typed-action-aware, behavior-aware, trajectory-aware, offer-aware, and learning-capable.
- Full-portfolio proof now exists, including product-ready coverage, reality-gap audit, and demo representativeness diagnostics.
- The highest-leverage next step is now Phase 18: a controlled translation layer that turns engine output into analyst- and buyer-ready product narratives without hiding technical truth.

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

### Pending Todos

None yet.

### Blockers/Concerns

- The local `gsd-tools.cjs` helper is still missing internal modules, so some GSD workflow helpers remain manual
- The website exists as a brownfield surface with live and curated demo seams, but its proof language is still ahead of full-portfolio validation
- Some recent website demo work is still uncommitted outside `.planning`; milestone-definition work should avoid mixing with those unrelated edits

## Session Continuity

Last session: 2026-03-18
Stopped at: Phase 18 planning complete; next step is `$gsd-execute-phase 18`
Resume file: None
