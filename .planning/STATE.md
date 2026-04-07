---
gsd_state_version: 1.0
milestone: v2.5
milestone_name: Recoverable Customer Targeting & Movement Optimization
status: active
stopped_at: Phase 62 complete; ready to plan Phase 63
last_updated: "2026-04-07T21:32:43+03:00"
last_activity: 2026-04-07
progress:
  total_phases: 64
  completed_phases: 60
  total_plans: 3
  completed_plans: 3
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-05)

**Core value:** Generate customer-specific credit action plans that are actionable, behaviorally realistic, governance-safe, and measurably useful enough to improve denied-customer outcomes without breaking enterprise trust.
**Current focus:** Phase 63 planning after Phase 62 classifier execution

## Current Position

Phase: 62 complete
Plan: 62-03 complete
Status: Recoverable classifier shipped; ready for Phase 63
Last activity: 2026-04-07 — Phase 62 executed and verified

## Performance Metrics

**Velocity:**

- Total plans completed: 176 (historical import + phases 8-25 + phases 30-39 + phases 40-44 + post-v2.1 phase 42.5 + phases 45-62)
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
| v2.2 completed milestone | 12 | phases 45-48 complete; archived | n/a |
| v2.3 completed milestone | 12 | phases 49-52 complete; archived | n/a |
| v2.4 completed milestone | 19 | phases 54-60 complete; archived | n/a |
| v2.5 active milestone | 6 | phases 61-62 complete | n/a |

**Recent Trend:**

- Milestone \`v2.3\` remains the shipped proof that bounded threshold and outcome tuning cannot create safe uplift on the old surface.
- Milestone \`v2.4\` is now archived as a shipped capability-expansion milestone with phases \`54-60\` complete.
- The shipped system now has canonical action semantics, deterministic feature mapping, safe DICE/rule-lane expansion, deterministic pathing/rendering, and cohort-level evidence packaging.
- Milestone \`v2.5\` now opens as a targeting and movement-optimization milestone focused on recoverable customers rather than broad recommendation expansion.
- Phase \`61 Recoverability Signal Definition\` now ships one canonical recoverability helper, additive runtime and collection propagation, and cohort-visible signal reporting without introducing recoverable classification or gating.
- Phase \`62 Recoverable Customer Classifier\` now ships one conservative classifier seam, additive runtime/collection/cohort propagation, and analyst-auditable classifier evidence without introducing routing, planner, or narrative drift.

## Accumulated Context

### Decisions

Recent decisions affecting the shipped baseline:

- \`v1.2 Recommendation Quality Hardening\` remains the shipped recommendation-quality baseline
- \`v1.3 Portfolio Intelligence & Productization\` remains the shipped productization baseline
- \`v2.0 Personalized Action & Decision Intelligence\` turned feature-delta outputs into semantic, numeric, feasible, execution-aware, and institution-aware plans
- \`v2.1 Decision Ownership & Pilot-Ready Trust\` turned those plans into deterministic decisions, reviewable funnels, operator packets, and repeatable pilot-refresh artifacts
- Post-v2.1 Phase \`42.5 Recommendation Validity Layer\` now prevents directionally wrong or no-op numeric recommendations from winning and marks suspicious numeric recommendations for bounded manual review
- Phase \`45 Winner Integrity Hard Stop\` now removes fallback path, widens only to valid pools, and records explicit \`no_valid_winner\` outcomes
- Phase \`46 Dice Lane Validity Enforcement\` converges DICE onto shared action contract
- Phase \`47 Selected Surface Consistency\` ships consumer-safe selected overlay
- Phase \`49 Threshold Policy Evaluation & Provenance\` proves shipped baseline should not be loosened through bounded threshold-only changes
- Phase \`50 Offer & Readiness Outcome Rules\` proves existing offer and readiness signals evaluated through bounded rules still end in explicit \`no_safe_uplift\`
- Phase \`51 Funnel Movement Guardrails & Evidence\` proves cohort limitation under current bounded signal set
- Phase \`52 Preferred Policy Baseline & Demo Proof\` pushes current baseline forward for demo docs and publishes non-adoption reason
- Phase \`54 Action Semantics Taxonomy\` establishes the canonical typed action taxonomy baseline for the v2.4 expansion
- Phase \`55 Feature → Action Mapping\` adds deterministic feature-to-action coverage, explicit non-actionable reason codes, and a reusable mapping inventory without widening the current runtime actionable set
- Phase \`56 DICE Action Space Expansion\` moves DICE onto an explicit first-wave runtime contract for loan amount, refinance, verification, and anchored delinquency actions while preserving winner integrity and downstream surface coherence
- Phase \`57 Heuristic / Institution Action Lane\` adds a deterministic institution/hybrid rule lane, explicit rule-quality gating, and actionable-only winner selection while preserving shared trust surfaces
- Phase \`58 Multi-Path Recourse Generation\` adds deterministic path identity, grouped alternative-path artifacts, selected-path traceability, and duplicate-resistant path metrics above the existing validated candidate pool
- Phase \`59 Action Semantics Rendering\` adds one deterministic render core for selected actions and grouped paths, propagates shared render payloads through artifacts, and keeps empty-state trust behavior explicit
- Phase \`60 Validation & Cohort Evaluation\` adds one cohort-evidence seam for denied, high-risk denied, and pilot-mixed population reporting while keeping trust proof separate from diversity evidence
- Phase \`62 Recoverable Customer Classifier\` adds one explicit recoverable decision rule over the shipped Phase 61 signal, preserves classifier truth across runtime and audit artifacts, and proves the classifier remains deterministic and fail-closed
- The website remains a typed consumer of engine artifacts.
- Pilot integration remains export-first and controlled.
- The next milestone should focus on outcome proof over the shipped \`v2.4\` surface rather than broadening semantics again immediately.

### Pending Todos

- Plan Phase `63` with `$gsd-discuss-phase 63`
- Keep recoverability deterministic and explainable; do not reopen model retraining, new action-type scope, or premature narrative work during v2.5

### Tooling / Tech Debt

- The local \`gsd-tools.cjs\` helper currently fails because \`.codex/get-shit-done/bin/gsd-tools.cjs\` cannot resolve missing \`./lib/core.cjs\`.
- Until that bundle is repaired, GSD orchestration fallback is manual.

### Blockers/Concerns

- Some Phase 41-44 validation frontmatter still understates \`wave_0_complete\` despite shipped tests and successful audit coverage.
- Large-sample reruns for v2.2 still produced zero \`no_valid_winner\` cases, so empty-state packet behavior remains proven by targeted automated tests rather than cohort evidence.

## Session Continuity

Last session: 2026-04-07T21:32:43+03:00
Stopped at: Phase 62 complete and verified; Phase 63 is next
Resume file: .planning/ROADMAP.md
