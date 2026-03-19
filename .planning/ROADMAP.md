# Roadmap: Credit Coach

## Milestones

- ✅ **v1.0 Brownfield Baseline** - Phases 1-7 (historical baseline reconstructed from imported docs, shipped 2026-03-10)
- ✅ **v1.1 Fairness Stability & KPI Hardening** - Phases 8-11 (completed 2026-03-15)
- ✅ **v1.2 Recommendation Quality Hardening** - Phases 12-16 (completed 2026-03-16)
- 🚧 **v1.3 Portfolio Intelligence & Productization** - Phases 17-21 (behavior and trajectory hardening re-added after post-18 resequencing; milestone opened 2026-03-17)

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

**Goal**: Prove the engine across the full portfolio, translate technical outputs into institution-ready narratives, harden execution and trajectory truth where product credibility demands it, stabilize artifact-driven website surfaces, and reach analyst- and pilot-ready product credibility.
**Phases**: 17-21 currently defined
**Status**: Active, Phases 17-21 complete; milestone audit found remaining website and ops gaps

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
**Plans**: 3 complete

Plans:
- [x] 19-01: Harden execution-probability posture, burden-horizon penalties, and composite or dual-realization semantics
- [x] 19-02: Strengthen execution-aware ranking leverage, high-risk ordering, and provisional contender penalties
- [x] 19-03: Reframe behavior-aware artifacts and review around nominal-vs-execution-aware value and risk-band evidence

### Phase 20: Trajectory Hardening

**Goal**: Harden the inherited trajectory layer into a deterministic, checkpoint-safe, product-ready planning contract that keeps short-term health, monotonicity, and replan behavior under control.
**Depends on**: Phase 19
**Plans**: 3 complete

Plans:
- [x] 20-01: Lock deterministic phase and checkpoint contracts across all roadmap outputs
- [x] 20-02: Harden trajectory consistency, soft monotonicity, and early-health protection
- [x] 20-03: Make replan logic, trajectory status, and policy labels deterministic and execution-layer aligned

Planned scope:
- Canonical phase assignment:
  - every action has exactly one `primary_phase`
  - multi-phase or ambiguous phase assignment is disallowed
- Fixed phase set:
  - `phase_1_stabilize` (`0-4w`)
  - `phase_2_build` (`4-12w`)
  - `phase_3_optimize` (`12-24w`)
- Fixed checkpoint set:
  - `week 4` / `primary`
  - `week 12` / `confirmation`
  - `week 24` / `stability`
- Each checkpoint must carry:
  - `checkpoint_type`
  - `predicted_pd`
  - `pd_delta`
  - `gate_pass_estimate`
  - `status`
- Soft monotonicity hardening:
  - `4w >= 12w >= 24w` as the default expectation
  - small drift tolerated, large jumps flagged
- Deterministic trajectory flags:
  - `trajectory_jump_flag`
  - `non_monotonic_flag`
  - `checkpoint_inconsistency_flag`
- Early-health protection:
  - weak `4w` health prevents a plan from reading as strong
- Deterministic replan boundaries:
  - allowed only at `week 4`, `week 12`, `week 24`
- Stable trajectory status:
  - `on_track`
  - `needs_replan`
  - `degraded`
- Rule-based policy labels:
  - `stabilize_first`
  - `balanced_progress`
  - `long_horizon_heavy`
- Phase 19 alignment:
  - `plan_execution_probability` and approval-dependent realization stay visible in trajectory evaluation

### Phase 21: Portfolio Proof & Product Confidence

**Goal**: Re-run the hardened engine across the full portfolio, refresh proof artifacts, and answer the product-facing question of whether the system is truly working beyond curated stories.
**Depends on**: Phase 20
**Plans**: 3 complete

Plans:
- [x] 21-01: Refresh the canonical portfolio proof with product-facing verdict, confidence, and Phase 17 baseline comparison
- [x] 21-02: Carry refreshed proof through suite packaging and emit one curated engine-owned confidence snapshot
- [x] 21-03: Switch website proof surfaces to the curated proof snapshot and typed proof contract

Planned scope:
- run the full portfolio again after trajectory hardening
- regenerate proof artifacts and website-facing confidence surfaces
- measure whether hardened trajectory behavior improves real cohort credibility
- produce a clearer “is this working?” answer for proof and product surfaces

### Post-21 Sequence

**Status**: Milestone closeout blocked pending gap planning

Notes:
- Phase 19, Phase 20, and Phase 21 are now the canonical near-term `v1.3` sequence.
- Additional work after Phase 21 remains intentionally undefined until the next redesign pass.
- This milestone remains active for gap planning and closeout; all currently defined `v1.3` phases are complete, but milestone audit found unresolved requirement gaps.

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
| 19. Behavior-Aware Recourse | v1.3 | 3/3 | Complete | 2026-03-19 |
| 20. Trajectory Hardening | v1.3 | 3/3 | Complete | 2026-03-19 |
| 21. Portfolio Proof & Product Confidence | v1.3 | 3/3 | Complete | 2026-03-19 |
