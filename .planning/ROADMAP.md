# Roadmap: Credit Coach

## Milestones

- ✅ **v1.0 Brownfield Baseline** - Phases 1-7 (historical baseline reconstructed from imported docs, shipped 2026-03-10)
- ✅ **v1.1 Fairness Stability & KPI Hardening** - Phases 8-11 (completed 2026-03-15)
- 🎯 **v1.2 Recommendation Quality Hardening** - Phases 12-16 (active)

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

<details>
<summary>✅ v1.1 Fairness Stability & KPI Hardening (Phases 8-11) - SHIPPED 2026-03-15</summary>

Historical archive: `.planning/milestones/v1.1-ROADMAP.md`

- Phase 8: Fairness Stability Matrix
- Phase 9: KPI Contract Unification
- Phase 10: Candidate Quality and Trajectory Tuning
- Phase 11: Release Evidence and Outcome Feedback

</details>

### 🎯 v1.2 Recommendation Quality Hardening (Active)

**Milestone Goal:** Improve the real-world validity, feasibility, and behavioral realism of recourse recommendations by expanding action semantics, modeling action execution probability, enabling sequential trajectory planning, introducing offer policy optimization, and establishing outcome feedback loops.

This milestone upgrades the system from a gate-aware recourse engine toward a behavior-aware sequential recourse decision engine.

#### Phase 12: Action Realism & Feasibility Expansion
**Goal**: Expand the action space from feature edits to real-world financial and institutional actions, and strengthen feasibility constraints.
**Depends on**: Phase 11 / v1.1 baseline
**Requirements**: [REC-01, REC-02, REC-03]
**Success Criteria** (what must be TRUE):
  1. Action taxonomy supports behavioral, structural, and institutional actions.
  2. Feasibility constraints prevent unrealistic financial transitions.
  3. Action diversity increases without raising infeasible-plan rate.
**Plans**: 3 plans

Plans:
- [x] 12-01: Redesign the action taxonomy for behavioral, structural, and institutional plan actions
- [x] 12-02: Expand feasibility realism with monthly, income, utilization, and financial-capacity constraints
- [x] 12-03: Add action dependency and conflict modeling for incompatible recommendation combinations

#### Phase 13: Behavior-Aware Recourse
**Goal**: Introduce execution probability modeling so recommendations consider the likelihood that a user will actually perform the suggested actions.
**Depends on**: Phase 12
**Requirements**: [REC-04, REC-05]
**Success Criteria** (what must be TRUE):
  1. Each action includes an estimated execution probability.
  2. Planner scoring incorporates expected utility.
  3. High-risk plans prioritize feasible, likely actions.
**Plans**: 3 plans

Plans:
- [x] 13-01: Add an action-execution probability model and planner integration
- [x] 13-02: Update planner scoring to use expected utility under gate constraints
- [x] 13-03: Simulate partial execution, failed steps, and mixed-execution scenarios

#### Phase 14: Sequential Recourse Planning
**Goal**: Transition from single-plan recommendations to multi-phase improvement trajectories.
**Depends on**: Phase 13
**Requirements**: [REC-06, REC-07]
**Success Criteria** (what must be TRUE):
  1. Plans include multiple time phases.
  2. Trajectory simulations capture dynamic risk evolution.
  3. Short-term improvements do not harm long-term outcomes.
**Plans**: 3 plans

Plans:
- [x] 14-01: Build a multi-phase planning model for near-, mid-, and longer-horizon actions
- [x] 14-02: Add dynamic trajectory simulation with timing, inertia, and partial execution
- [x] 14-03: Balance short-term feasibility against long-term risk improvement in the optimization objective

#### Phase 15: Policy Optimization Layer
**Goal**: Integrate institutional offer optimization with recourse planning.
**Depends on**: Phase 14
**Requirements**: [REC-08, REC-09]
**Success Criteria** (what must be TRUE):
  1. Institution-side offers appear in candidate plans.
  2. Offer acceptance likelihood is modeled.
  3. Recovery proxies improve without increasing risk violations.
**Plans**: 3 plans

Plans:
- [ ] 15-01: Add institution-side offer actions into the recourse action space
- [ ] 15-02: Score offers against expected recovery, risk, fairness, and reliability constraints
- [ ] 15-03: Model user acceptance probability for offers and fold it into expected recovery

#### Phase 16: Outcome Feedback & Learning Loop
**Goal**: Enable the system to learn from real-world outcomes.
**Depends on**: Phase 15
**Requirements**: [REC-10, REC-11]
**Success Criteria** (what must be TRUE):
  1. Decisions and recommendations are logged with full context.
  2. Outcome ingestion updates evaluation datasets.
  3. Policy evaluation supports off-policy analysis.
**Plans**: 3 plans

Plans:
- [ ] 16-01: Expand decision logging to capture recommendation, offer, and execution context
- [ ] 16-02: Build an outcome-ingestion pipeline for action completion, payment behavior, default, and recovery signals
- [ ] 16-03: Add off-policy evaluation tooling such as IPS and doubly robust reporting

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
| 9. KPI Contract Unification | v1.1 | 3/3 | Complete | 2026-03-14 |
| 10. Candidate Quality and Trajectory Tuning | v1.1 | 3/3 | Complete | 2026-03-15 |
| 11. Release Evidence and Outcome Feedback | v1.1 | 3/3 | Complete | 2026-03-15 |
| 12. Action Realism & Feasibility Expansion | v1.2 | 3/3 | Complete | 2026-03-15 |
| 13. Behavior-Aware Recourse | v1.2 | 3/3 | Complete | 2026-03-16 |
| 14. Sequential Recourse Planning | v1.2 | 3/3 | Complete | 2026-03-16 |
| 15. Policy Optimization Layer | v1.2 | 0/3 | Pending | - |
| 16. Outcome Feedback & Learning Loop | v1.2 | 0/3 | Pending | - |
