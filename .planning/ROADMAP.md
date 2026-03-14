# Roadmap: Credit Coach

## Milestones

- ✅ **v1.0 Brownfield Baseline** - Phases 1-7 (historical baseline reconstructed from imported docs, shipped 2026-03-10)
- 🚧 **v1.1 Fairness Stability & KPI Hardening** - Phases 8-11 (current milestone)

<details>
<summary>✅ v1.0 Brownfield Baseline (Phases 1-7) - SHIPPED 2026-03-10</summary>

Historical archive: `.planning/milestones/v1.0-ROADMAP.md`

- Phase 1: Modeling Foundation Lock
- Phase 2: Gate-Aligned Recourse Core
- Phase 3: Trajectory and High-Risk Optimization
- Phase 4: Explainability and Decision Diagnostics
- Phase 5: Evaluation and Benchmark Matrix
- Phase 6: Production Hardening and Governance
- Phase 7: KPI Gate Stabilization

</details>

### 🚧 v1.1 Fairness Stability & KPI Hardening (In Progress)

**Milestone Goal:** Make release decisions stable across repeated seeded runs by hardening fairness diagnostics, KPI contract alignment, candidate-quality evidence, and telemetry-backed release packages.

#### Phase 8: Fairness Stability Matrix
**Goal**: Build the fairness-stability evidence needed to understand and control seeded regressions.
**Depends on**: Phase 7
**Requirements**: [FAIR-01, FAIR-02, FAIR-03]
**Completed**: 2026-03-14
**Success Criteria** (what must be TRUE):
  1. Seeded fairness summaries exist for approval, EO, recourse success, and high-stress outcomes.
  2. Fairness failures can be localized by segment, risk band, and candidate source.
  3. Fairness-aware controls can be tuned without losing diagnostic traceability.
**Plans**: 3 plans

Plans:
- [x] 08-01: Standardize multi-seed fairness summary and aggregate artifacts
- [x] 08-02: Add intersecting segment and source-level regression diagnostics
- [x] 08-03: Harden fairness-aware ranking or quota controls under the shared contract

#### Phase 9: KPI Contract Unification
**Goal**: Align smoke, phase-suite, and challenger workflows behind one deterministic acceptance contract.
**Depends on**: Phase 8
**Requirements**: [KPI-01, KPI-02, KPI-03]
**Success Criteria** (what must be TRUE):
  1. Smoke, suite, and challenger outputs use the same threshold meanings and pass/fail semantics.
  2. Seeded experiment runs can freeze model state and compare like-for-like artifacts.
  3. Milestone acceptance depends on repeated seeded evidence instead of a single winning run.
**Plans**: 3 plans

Plans:
- [ ] 09-01: Extract and align shared KPI contract helpers across release runners
- [ ] 09-02: Standardize train-once or frozen-model seeded suite execution
- [ ] 09-03: Build milestone acceptance summaries from repeated seeded evidence

#### Phase 10: Candidate Quality and Trajectory Tuning
**Goal**: Improve the quality and explainability of candidate generation once the measurement contract is stable.
**Depends on**: Phase 9
**Requirements**: [CAND-01, CAND-02, CAND-03]
**Success Criteria** (what must be TRUE):
  1. Candidate diversity and source entropy are measured in milestone evidence.
  2. Short-term phase-1 progress can be tuned safely for denied high-risk users.
  3. Reports explain which generator or policy changes improved or harmed KPI outcomes.
**Plans**: 3 plans

Plans:
- [ ] 10-01: Instrument candidate diversity and generator provenance metrics
- [ ] 10-02: Harden short-term phase-1 fast-track tuning for high-risk paths
- [ ] 10-03: Publish generator and policy impact diagnostics beside batch KPIs

#### Phase 11: Release Evidence and Outcome Feedback
**Goal**: Make production-like release evidence complete, reproducible, and connected to business-impact proxies.
**Depends on**: Phase 10
**Requirements**: [OPS-01, OPS-02, OPS-03]
**Success Criteria** (what must be TRUE):
  1. Production profile fails closed when telemetry evidence is missing or unhealthy.
  2. Release packets include fairness, trajectory, telemetry, and seed-summary artifacts in stable locations.
  3. Outcome-feedback or policy-delta reports connect offline KPI movement to business-impact proxies.
**Plans**: 3 plans

Plans:
- [ ] 11-01: Enforce telemetry-required production profile and exporter health checks
- [ ] 11-02: Standardize reproducible release evidence packs and milestone decision bundles
- [ ] 11-03: Build outcome-feedback and policy-delta reporting workflow

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Modeling Foundation Lock | v1.0 | 3/3 | Complete | 2026-03-10 |
| 2. Gate-Aligned Recourse Core | v1.0 | 3/3 | Complete | 2026-03-10 |
| 3. Trajectory and High-Risk Optimization | v1.0 | 3/3 | Complete | 2026-03-10 |
| 4. Explainability and Decision Diagnostics | v1.0 | 2/2 | Complete | 2026-03-10 |
| 5. Evaluation and Benchmark Matrix | v1.0 | 3/3 | Complete | 2026-03-10 |
| 6. Production Hardening and Governance | v1.0 | 3/3 | Complete | 2026-03-10 |
| 7. KPI Gate Stabilization | v1.0 | 3/3 | Complete | 2026-03-10 |
| 8. Fairness Stability Matrix | v1.1 | 3/3 | Complete | 2026-03-14 |
| 9. KPI Contract Unification | v1.1 | 0/3 | Not started | - |
| 10. Candidate Quality and Trajectory Tuning | v1.1 | 0/3 | Not started | - |
| 11. Release Evidence and Outcome Feedback | v1.1 | 0/3 | Not started | - |
