# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-17)

**Core value:** Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints, then surface those plans in a form that enterprise buyers and analysts can trust.
**Current focus:** `v1.3 Portfolio Intelligence & Productization`

## Current Position

Phase: 25 - Pilot Readiness & Demo Ops Baseline
Plan: phase complete
Status: Phase 25 executed - v1.3 ready for final milestone audit
Last activity: 2026-03-20 - Executed pilot-readiness baseline, closing `OPS-02` with structured intake, explicit pilot docs, and a curated demo handoff pack

Progress: Phases 17-25 complete; all v1.3 requirements are now satisfied

## Performance Metrics

**Velocity:**
- Total plans completed: 72
- Average duration: historical data not reconstructed
- Total execution time: historical data not reconstructed

**By Milestone:**

| Milestone | Plans | Total | Status |
|-----------|-------|-------|--------|
| v1.0 historical baseline | 20 | historical import | Complete |
| v1.1 completed milestone | 12 | phases 8-11 complete | Complete |
| v1.2 completed milestone | 15 | phases 12-16 complete | Complete |
| v1.3 active milestone | 28 complete | phases 17-25 complete; ready for final milestone audit and closeout | Open |

**Recent Trend:**
- The engine remains typed-action-aware, behavior-aware, trajectory-aware, offer-aware, and learning-capable.
- Full-portfolio proof, curated confidence packaging, and typed buyer-facing roadmap narratives are all now in place.
- Phase 19 and Phase 20 re-hardened execution-aware ranking and deterministic trajectory contracts.
- Phase 21 refreshed the canonical proof seam and shipped the engine-owned `product_confidence_snapshot.json`.
- Phase 22 turned the Demo Center into an executive-first buyer surface with calmer UI, reduced KPI density, CTA seams, and technical detail on demand.
- Phase 23 closed `WEB-03` by shipping:
  - one shared Proof and Investor vocabulary seam
  - a verdict-first Proof page with compact trust rail and translated benchmark language
  - an Investor page that reads market pain -> wedge -> proof -> monetization
  - second-layer `decision intelligence infrastructure` positioning and default `pilot -> platform` commercial framing
- Phase 24 closed `OPS-01` by shipping:
  - one analyst UAT matrix with an explicit pass or caution or fail gate
  - one route-level walkthrough runbook tied to `/demo` and `/proof`
  - one milestone-local results packet that records five of five analyst tasks as pass
- Phase 25 closed `OPS-02` by shipping:
  - one structured pilot-intake contract across the contact surface and inbound pipeline
  - one explicit `PILOT_READINESS.md` baseline for runtime, persistence, and auth posture
  - one `CURATED_DEMO_HANDOFF.md` playbook that maps intake into `/demo` and `/proof`
- The 2026-03-19 milestone audit gaps on `WEB-01`, `WEB-02`, `WEB-03`, `OPS-01`, and `OPS-02` are now closed.
- The milestone is now ready for final audit and closeout.

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
- Phase 17 established the canonical portfolio proof seam and the full-cohort coverage vocabulary.
- Phase 18 established the engine-owned narrative contract with executive summary by default and technical reveal on demand.
- Phase 19 re-hardened conservative execution truth and stronger execution-aware ranking behavior.
- Phase 20 locked the deterministic 4w/12w/24w trajectory and checkpoint contract.
- Phase 21 shipped product-facing proof verdicts, confidence labels, and the curated `product_confidence_snapshot.json`.
- Phase 22 shipped the buyer-first Demo Center refactor and closed `WEB-02`.
- Phase 23 shipped the shared proof/investor vocabulary seam, the executive-memo Proof page, and the disciplined Investor brief, closing `WEB-03`.
- Phase 24 defines analyst validation through a matrix, a runbook, and milestone-local results rather than generic UX feedback.
- Phase 25 defines buyer handoff readiness through structured intake, an explicit ops baseline, and a curated demo playbook.

### Roadmap Evolution

- Phase 19 added: Behavior-Aware Recourse
- Phase 20 re-scoped: Trajectory Hardening (mini phase)
- Phase 21 added: Portfolio Proof & Product Confidence
- Phase 22 executed: Business-First Demo Center Refactor
- Phase 23 executed: Proof & Investor Narrative Hardening
- Phase 24 executed: Analyst Workflow & UAT Validation
- Phase 25 executed: Pilot Readiness & Demo Ops Baseline

### Pending Todos

None yet.

### Blockers/Concerns

- The local `gsd-tools.cjs` helper is still missing internal modules, so some GSD workflow helpers remain manual
- The website now has buyer-safe, analyst-safe, and pilot-baseline surfaces, but milestone archival still depends on final audit and closeout
- Some recent website demo work is still uncommitted outside `.planning`; milestone-definition work should avoid mixing with those unrelated edits

## Session Continuity

Last session: 2026-03-20
Stopped at: Completed Phase 25 execution; next step is `$gsd-audit-milestone`
Resume file: .planning/ROADMAP.md
