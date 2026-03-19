# Roadmap: Credit Coach

## Milestones

- ✅ **v1.0 Brownfield Baseline** - Phases 1-7 (historical baseline reconstructed from imported docs, shipped 2026-03-10)
- ✅ **v1.1 Fairness Stability & KPI Hardening** - Phases 8-11 (completed 2026-03-15)
- ✅ **v1.2 Recommendation Quality Hardening** - Phases 12-16 (completed 2026-03-16)
- 🚧 **v1.3 Portfolio Intelligence & Productization** - Phases 17-20 (behavior and trajectory hardening re-added after post-18 resequencing; milestone opened 2026-03-17)

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

<details>
<summary>✅ v1.2 Recommendation Quality Hardening (Phases 12-16) - SHIPPED 2026-03-16</summary>

Historical archive: `.planning/milestones/v1.2-ROADMAP.md`

- Phase 12: Action Realism & Feasibility Expansion
- Phase 13: Behavior-Aware Recourse
- Phase 14: Sequential Recourse Planning
- Phase 15: Policy Optimization Layer
- Phase 16: Outcome Feedback & Learning Loop

</details>

## Active Milestone

### v1.3 Portfolio Intelligence & Productization

**Goal**: Prove the engine across the full portfolio, translate technical outputs into institution-ready narratives, stabilize artifact-driven website surfaces, and reach analyst- and pilot-ready product credibility.
**Phases**: 17-20 currently defined
**Status**: Active, Phases 17-18 complete; Phases 19-20 added and awaiting planning

### Phase 17: Full Portfolio Evaluation & Coverage Audit

**Goal**: Run the engine across the full evaluation population and quantify coverage, feasibility, execution-weighted improvement, offer reach, checkpoint health, and governance-safe rates across segments.
**Depends on**: Phase 16
**Plans**: 3 complete

Plans:
- [x] 17-01: Build a full-population evaluation runner and canonical portfolio coverage tables
- [x] 17-02: Add segment-level reporting for risk, income, stress, trajectory, offer, and readiness slices
- [x] 17-03: Publish a portfolio validation review that separates curated demo stories from full-cohort proof

### Phase 18: Decision Narrative & Product Output Translation

**Goal**: Build a controlled translation layer that turns engine output into analyst-friendly and buyer-friendly product narratives, with executive summaries by default and expandable technical traceability on demand.
**Depends on**: Phase 17
**Plans**: 3 complete

Plans:
- [x] 18-01: Define the narrative contract and action template library for action summaries, why-it-matters, expected outcomes, and executive summary cards
- [x] 18-02: Add controlled technical reveal, checkpoint or offer or adverse-action narration, narrative confidence, and vocabulary consistency layers
- [x] 18-03: Validate one UI-ready output schema across representative cases so website and analyst surfaces can consume the same business-first narrative contract

### Phase 19: Behavior-Aware Recourse

**Goal**: Re-open the inherited behavior-aware ranking layer as an explicit v1.3 hardening target so recommendation quality reflects not only nominal PD improvement but also whether customers are likely to execute the plan.
**Depends on**: Phase 18
**Plans**: Not planned yet

Planned scope:
- Establish an explicit `action_execution_probability` and `plan_execution_probability` contract for all rankable plans
- Add composite-action aggregation, provisional or approval-pending handling, and execution scenario classes such as full, mixed, and failed execution
- Reconfirm that expected utility affects ranking as a tie-break or ordering layer rather than a hard gate, and emit canonical behavior-aware evidence artifacts

### Phase 20: Sequential / Trajectory Planning

**Goal**: Re-open the inherited phased-roadmap layer as an explicit v1.3 hardening target so plans remain understandable, checkpoint-driven, and safe over time rather than behaving like one-shot recommendations.
**Depends on**: Phase 19
**Plans**: Not planned yet

Planned scope:
- Finalize canonical `phases[]`, three fixed planning stages, and one primary phase per action
- Reconfirm checkpoint semantics at 4w, 12w, and 24w, along with soft monotonicity expectations and controlled replan boundaries
- Tighten trajectory status and policy-label semantics so roadmap outputs and checkpoint reviews stay product-ready and business-readable

### Post-20 Sequence

**Status**: Still intentionally open

Notes:
- Phase 19 and Phase 20 are now canonical again under `v1.3`.
- Additional work after Phase 20 remains intentionally undefined until the next redesign pass.
- This milestone remains active, with portfolio proof and narrative translation complete and the next hardening wave queued.

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
| 15. Policy Optimization Layer | v1.2 | 3/3 | Complete | 2026-03-16 |
| 16. Outcome Feedback & Learning Loop | v1.2 | 3/3 | Complete | 2026-03-16 |
| 17. Full Portfolio Evaluation & Coverage Audit | v1.3 | 3/3 | Complete | 2026-03-18 |
| 18. Decision Narrative & Product Output Translation | v1.3 | 3/3 | Complete | 2026-03-18 |
| 19. Behavior-Aware Recourse | v1.3 | 0/0 | Planned | - |
| 20. Sequential / Trajectory Planning | v1.3 | 0/0 | Planned | - |
