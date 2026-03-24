# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-23)

**Core value:** Generate customer-specific credit action plans that are actionable, behaviorally realistic, governance-safe, and measurably useful enough to improve denied-customer outcomes without breaking enterprise trust.
**Current focus:** post-v2.1 carry-forward closeout complete

## Current Position

Phase: post-v2.1 carry-forward
Plan: phase 42.5 complete
Status: Ready for next milestone definition
Last activity: 2026-03-24 - Closed Phase `42.5 Recommendation Validity Layer`; code and regression validation passed, full processed-data artifact rerun validation deferred because `credit-coach/data/processed/test.parquet` is missing locally

Progress: `v2.1` remains the shipped and audited milestone baseline. Post-shipment Phase `42.5` now adds canonical numeric recommendation validity, hard-invalid winner filtering, warning penalties, operator manual-review badges, explanation-pack human-review propagation, and additive collection metrics without reopening decision ownership, calibration math, or operator packet semantics.

## Performance Metrics

**Velocity:**
- Total plans completed: 126 (historical import + phases 8-25 + phases 30-39 + phases 40-44 + post-v2.1 phase 42.5)
- Average duration: historical data not reconstructed
- Total execution time: historical data not reconstructed

**By Milestone:**

| Milestone | Plans | Total | Avg/Plan |
|-----------|-------|-------|----------|
| v1.0 historical baseline | 20 | historical import | n/a |
| v1.1 completed milestone | 12 | phases 8-11 complete | n/a |
| v1.2 completed milestone | 15 | phases 12-16 complete | n/a |
| v1.3 completed milestone | 28 | phases 17-25 complete | n/a |
| v2.0 completed milestone | 30 | phases 30-39 complete | n/a |
| v2.1 completed milestone | 18 | phases 40, 40.5, 41, 43, 42, 44 complete | n/a |
| post-v2.1 carry-forward hardening | 3 | phase 42.5 complete | n/a |

**Recent Trend:**
- Credit Coach now carries one continuous stack from semantic action planning to pilot-facing package delivery.
- Buyer-safe and analyst-safe surfaces remain typed consumers of engine-owned truth rather than alternate logic layers.
- Portfolio proof can now speak about personalized numeric burden, realization, calibration, and pilot readiness.
- Phase 40 now guarantees null-free summary truth, raw-flat parity checks, zero-step rejection, and business-facing consumer alignment to canonical summary fields.
- Phase 40.5 now adds deterministic internal-vs-external decision ownership, subtype truth, confidence gating, and business-safe three-state consumer surfaces.
- Phase 41 now ships cohort semantics, funnel/readiness measurement, shadow calibration, and additive calibration packaging under the same collection run root.
- Phase 43 now ships a derived operator-surface lane with per-customer packets, collection-level review briefing, and a strict business-safe versus appendix-detail split.
- Phase 42 now ships explicit source truth, empty-contender removal, internal-vs-dice competitiveness metrics, and additive planner-quality summary signals.
- Phase 42.5 now hardens numeric recommendation trust with directional hard gates, economic warning penalties, contender filtering, operator warning badges, explanation-pack human-review propagation, and additive collection metrics.
- Phase 44 now ships repeatable pilot refresh orchestration, separate artifact QA versus portfolio smoke lanes, thin institution overlays, institution-facing explanation packs, and bounded proof-surface docs.
- Milestone `v2.1` audit passed with `12/12` requirements satisfied, `6/6` integrations, and `4/4` end-to-end flows.

## Accumulated Context

### Decisions

Recent decisions affecting the shipped baseline:

- `v1.2 Recommendation Quality Hardening` remains the shipped recommendation-quality baseline
- `v1.3 Portfolio Intelligence & Productization` remains the shipped productization baseline
- `v2.0 Personalized Action & Decision Intelligence` turned feature-delta outputs into semantic, numeric, feasible, execution-aware, and institution-aware plans
- `v2.1 Decision Ownership & Pilot-Ready Trust` turned those plans into deterministic decisions, reviewable funnels, operator packets, and repeatable pilot-refresh artifacts
- Post-v2.1 Phase `42.5 Recommendation Validity Layer` now prevents directionally wrong or no-op numeric recommendations from winning and marks suspicious numeric recommendations for bounded manual review
- The website remains a typed consumer of engine artifacts rather than a source of decision logic
- Portfolio proof now includes numeric impact and calibration honesty, not just product confidence
- Pilot integration remains export-first and controlled instead of pretending live connectivity
- Milestone audit for `v2.0` passed with `10/10` requirements satisfied, `9/9` integrations, and `5/5` end-to-end flows

### Pending Todos

None yet.

### Blockers/Concerns

- The local `gsd-tools.cjs` helper is still missing internal modules, so milestone-op automation requires manual fallback.
- Some Phase 41-44 validation frontmatter still understates `wave_0_complete` despite shipped tests and successful audit coverage.
- Full processed-data artifact rerun validation for Phase `42.5` is deferred locally until `credit-coach/data/processed/test.parquet` is restored.
- The next workflow step is `$gsd-new-milestone` to define post-v2.1 work.

## Session Continuity

Last session: 2026-03-24
Stopped at: Phase `42.5 Recommendation Validity Layer` closed; next step is `$gsd-new-milestone`
Resume file: None
