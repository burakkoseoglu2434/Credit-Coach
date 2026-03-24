# Requirements Snapshot: Credit Coach

No active milestone requirement set is currently open. This file captures the validated baseline and carry-forward requirement state between milestones.

## Validated

- ✓ Core PD modeling, calibration, and deterministic backend controls exist in the codebase - v1.0
- ✓ Gate-aligned recourse generation, feasibility controls, and high-risk or trajectory flows exist in the codebase - v1.0
- ✓ Fairness, stress, benchmark, challenger, telemetry, and release-gate workflows exist in the codebase - v1.0
- ✓ Seeded fairness, KPI contract, candidate-quality, telemetry evidence, and outcome-feedback packaging are hardened - v1.1
- ✓ Recommendation quality is now typed-action-aware, behavior-aware, trajectory-aware, offer-aware, and learning-loop-capable - v1.2
- ✓ Portfolio proof, business-first product surfaces, analyst validation, and pilot-baseline demo ops are now shipped and audited - v1.3
- ✓ Personalized action intelligence is now semantic, numeric, feasible, execution-aware, institution-aware, portfolio-validated, and pilot-package-ready - v2.0
- ✓ Deterministic decision ownership, contract trust repair, cohort calibration, operator review packs, planner source-mix honesty, and repeatable pilot refresh now ship together as one audited baseline - v2.1
- ✓ Post-v2.1 Phase `42.5 Recommendation Validity Layer` now hardens numeric recommendations with canonical validity evaluation, hard-invalid contender filtering, warning penalties, operator sanity badges, explanation-pack human-review propagation, and additive collection metrics

## Deferred Validation

- Phase `42.5 Recommendation Validity Layer` passed compile, focused pytest, broader regression, and diff-hygiene validation.
- Full processed-data artifact rerun validation is deferred locally until `credit-coach/data/processed/test.parquet` is restored.

## Active

- [ ] Institution-specific inbound and outbound integration contracts beyond export-first pilot packaging
- [ ] Compliance-adjacent explanation and governance workflows beyond bounded pilot support artifacts
- [ ] Recurring proof refresh, release review, and milestone health automation
- [ ] Milestone tooling and planning metadata cleanup so archive and audit workflows can run without manual fallback

## Out of Scope

- Full borrower-facing self-serve or mobile experiences until a future milestone explicitly opens them
- Fully autonomous online policy promotion before evidence-first controls are expanded
- Legal or compliance opinion automation
- Unscoped greenfield rewrites of the engine or website stacks

---
*Last updated: 2026-03-24 after closing Phase 42.5 Recommendation Validity Layer*
