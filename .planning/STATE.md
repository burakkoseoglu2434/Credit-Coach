# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-17)

**Core value:** Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints, then surface those plans in a form that enterprise buyers and analysts can trust.
**Current focus:** `v1.3 Portfolio Intelligence & Productization`

## Current Position

Phase: 21
Plan: 3/3 plans complete
Status: Ready for milestone audit
Last activity: 2026-03-19 - Executed Phase 21 proof verdict refresh, curated proof snapshot packaging, and proof-page sync

Progress: Phases 17-21 complete; `v1.3` is ready for milestone audit

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
| v1.3 active milestone | 15 complete | phases 17-21 complete, awaiting audit | Open |

**Recent Trend:**
- The recourse engine is already typed-action-aware, behavior-aware, trajectory-aware, offer-aware, and learning-capable.
- Full-portfolio proof now exists, including product-ready coverage, reality-gap audit, and demo representativeness diagnostics.
- The engine now emits buyer- and analyst-ready roadmap narratives directly, including executive summary, checkpoint meaning, reasons, and technical reveal.
- Behavior-aware recourse has now been re-hardened with conservative execution truth, stronger planner demotion, and nominal-vs-execution-aware executive evidence.
- The post-18 roadmap has been partially rebuilt: Phase 19 reopened behavior-aware recourse hardening, Phase 20 completed the deterministic trajectory contract hardening pass, and Phase 21 is reserved for proof refresh.
- Phase 21 is now shipped across three closed waves:
  - product-facing proof verdict and confidence over the canonical portfolio seam
  - suite-level curated `product_confidence_snapshot.json` packaging
  - proof-page sync to one engine-owned curated proof artifact
- Phase 20 is now shipped across three closed waves:
  - deterministic phase and checkpoint contract locking
  - consistency, monotonicity, and early-health hardening
  - deterministic replan, status, and policy-label semantics
- Phase 20 now leaves the engine with:
  - fixed `4 / 12 / 24` checkpoint semantics
  - explicit `on_track / at_risk / missed` checkpoint-local truth
  - weak-4w-sensitive planner behavior
  - boundary-only formal replan and stable trajectory labels
- Future work after Phase 21 remains intentionally open until the next redesign pass.

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
- On 2026-03-19, `Phase 19: Behavior-Aware Recourse` and `Phase 20: Trajectory Hardening` were added back as explicit hardening passes over inherited `v1.2` capability
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
- On 2026-03-19, Phase 20 was re-scoped into a mini hardening phase centered on:
  - deterministic phase assignment
  - fixed 4w or 12w or 24w checkpoint contracts
  - soft monotonicity and early-health protection
  - deterministic replan and trajectory status semantics
- On 2026-03-19, Phase 20 planning split the work into:
  - contract hardening for phases and checkpoints
  - consistency and soft-monotonicity hardening
  - deterministic replan, status, and policy-label hardening
- On 2026-03-19, Phase 20 discussion locked:
  - `phase_3_optimize` to `13-24w` / `3-6 ay`
  - checkpoint type enum to `primary | confirmation | stability`
  - checkpoint-local status enum to `on_track | at_risk | missed`
  - `24w` as the closing proof and product horizon
  - `0.01` monotonicity tolerance and `>0.03` worsening jump flag
  - weak `4w` health as dominant negative signal without hard reject
  - `needs_replan` only at canonical review boundaries and `degraded` as keep-going-no-longer-rational state
  - fully rule-based policy labels, with execution truth allowed only as a conservative secondary adjustment
- On 2026-03-19, Phase 21 was reintroduced as the next proof-facing pass:
  - rerun the hardened engine portfolio-wide
  - regenerate proof artifacts
  - answer the buyer-facing “is this really working?” question with refreshed evidence
- On 2026-03-19, Phase 21 discussion locked:
  - product-facing proof verdicts separate from internal release decisions
  - canonical verdict set `working | promising | mixed | not_proven`
  - separate proof confidence labels `strong | moderate | weak`
  - headline proof hierarchy centered on product-ready coverage, governance-safe coverage, and execution-aware value
  - `weak_4w` and delayed trajectory truth as first-class supporting proof
  - explicit delta versus the Phase 17 canonical proof baseline
  - website proof sync via one engine-derived curated proof snapshot
- On 2026-03-19, Phase 20 shipped:
  - locked `phase_3_optimize` to `13-24w` / `3-6 ay`
  - fixed checkpoint enums and machine-readable checkpoint-local status
  - explicit weak-4w, jump, non-monotonic, and inconsistency trajectory truth
  - boundary-only replan with safer `needs_replan` vs `degraded` separation
  - rule-based trajectory labels that remain checkpoint-first and only conservatively execution-adjusted
- On 2026-03-19, Phase 21 shipped:
  - product-facing proof verdicts and proof confidence in the canonical portfolio proof seam
  - explicit delta versus the Phase 17 proof baseline
  - one engine-owned `product_confidence_snapshot.json` for downstream proof consumers
  - a proof page that consumes one curated artifact instead of stitching many raw proof files

### Roadmap Evolution

- Phase 19 added: Behavior-Aware Recourse
- Phase 20 re-scoped: Trajectory Hardening (mini phase)
- Phase 21 added: Portfolio Proof & Product Confidence

### Pending Todos

None yet.

### Blockers/Concerns

- The local `gsd-tools.cjs` helper is still missing internal modules, so some GSD workflow helpers remain manual
- The website exists as a brownfield surface with live and curated demo seams, but its proof language is still ahead of full-portfolio validation
- Some recent website demo work is still uncommitted outside `.planning`; milestone-definition work should avoid mixing with those unrelated edits

## Session Continuity

Last session: 2026-03-19
Stopped at: Phase 21 complete; next step is milestone audit
Resume file: None
