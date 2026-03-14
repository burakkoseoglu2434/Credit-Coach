# Requirements: Credit Coach v1.1 Fairness Stability & KPI Hardening

**Defined:** 2026-03-14
**Core Value:** Generate credit recourse plans that are actionable, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints.

## v1.1 Requirements

### Fairness Stability

- [x] **FAIR-01**: System can compute repeated-seed fairness summaries for approval gap, equalized odds, recourse success gap, and high-stress fairness outcomes from one shared contract
- [x] **FAIR-02**: System can localize fairness regressions by intersecting segment, risk band, and candidate source rather than only aggregate metrics
- [x] **FAIR-03**: System can apply fairness-aware ranking or quota controls while keeping lift, gate-pass, and diagnostic evidence comparable

### KPI Contract

- [x] **KPI-01**: `run_production_smoke`, `run_phase_experiment_suite`, and `run_model_challenger_matrix` use aligned KPI thresholds and pass/fail semantics
- [x] **KPI-02**: Experiment suites can freeze training state so repeated seeded comparisons use the same model snapshot
- [x] **KPI-03**: Milestone acceptance is based on repeated seeded evidence rather than a single passing run

### Candidate Quality

- [x] **CAND-01**: Batch evaluation can measure candidate diversity and source entropy across internal and DiCE-driven plan generation paths
- [x] **CAND-02**: Planner and generator can prefer short-term phase-1 progress for denied high-risk customers when configured
- [x] **CAND-03**: Evaluation artifacts show which generator or policy changes improved or harmed gate pass, fairness, and short-term trajectory outcomes

### Operations & Outcome Feedback

- [ ] **OPS-01**: Production profile requires telemetry and fails closed when telemetry export is disabled or degraded
- [ ] **OPS-02**: Release evidence packs include fairness, trajectory, telemetry, and seed summary artifacts in reproducible locations
- [ ] **OPS-03**: System can publish outcome-feedback or policy-delta style reports linking offline KPI movement to business-impact proxies

## Future Requirements

### Productization

- **PROD-01**: Operator-facing dashboards summarize milestone health without reading raw artifacts
- **PROD-02**: Regulatory explanation layer expands from technical XAI outputs to user-facing adverse-action narratives
- **PROD-03**: Release review and milestone health checks run on a recurring automated schedule

## Out of Scope

| Feature | Reason |
|---------|--------|
| New end-user application surfaces | This milestone is focused on brownfield stability, not new product surface area |
| Replacing governance gates with lift-only optimization | Historical reports show this causes release regressions |
| Full online experimentation platform | Outcome feedback is milestone scope; full online experimentation remains later-stage work |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FAIR-01 | Phase 8 | Complete |
| FAIR-02 | Phase 8 | Complete |
| FAIR-03 | Phase 8 | Complete |
| KPI-01 | Phase 9 | Complete |
| KPI-02 | Phase 9 | Complete |
| KPI-03 | Phase 9 | Complete |
| CAND-01 | Phase 10 | Pending |
| CAND-02 | Phase 10 | Pending |
| CAND-03 | Phase 10 | Pending |
| OPS-01 | Phase 11 | Pending |
| OPS-02 | Phase 11 | Pending |
| OPS-03 | Phase 11 | Pending |

**Coverage:**
- v1.1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0

---
*Requirements defined: 2026-03-14*
*Last updated: 2026-03-14 after completing Phase 9*
