# Roadmap: Credit Coach

## Milestones

- ✅ **v1.0 Brownfield Baseline** - Phases 1-7 (historical baseline reconstructed from imported docs, shipped 2026-03-10)
- ✅ **v1.1 Fairness Stability & KPI Hardening** - Phases 8-11 (completed 2026-03-15)
- ✅ **v1.2 Recommendation Quality Hardening** - Phases 12-16 (completed 2026-03-16)
- ✅ **v1.3 Portfolio Intelligence & Productization** - Phases 17-25 (completed 2026-03-20)

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

<details>
<summary>✅ v1.3 Portfolio Intelligence & Productization (Phases 17-25) - SHIPPED 2026-03-20</summary>

Historical archive: `.planning/milestones/v1.3-ROADMAP.md`

- Phase 17: Full Portfolio Evaluation & Coverage Audit
- Phase 18: Decision Narrative & Product Output Translation
- Phase 19: Behavior-Aware Recourse
- Phase 20: Trajectory Hardening
- Phase 21: Portfolio Proof & Product Confidence
- Phase 22: Business-First Demo Center Refactor
- Phase 23: Proof & Investor Narrative Hardening
- Phase 24: Analyst Workflow & UAT Validation
- Phase 25: Pilot Readiness & Demo Ops Baseline

</details>

## Active Milestone

### v2.0 Personalized Action & Decision Intelligence

**Goal**: Turn model-level recourse outputs into customer-specific, numeric, feasible, and institution-aware action plans with clear product-ready narratives and portfolio-level validation.
**Phases**: 26-29 currently defined
**Status**: Active, requirements and roadmap defined; ready to start Phase 26

### Phase 26: Personalized Numeric Action Contracts

**Goal**: Convert selected recourse outputs into customer-specific numeric action contracts with explicit deltas, units, timing, and completion criteria.
**Depends on**: Phase 25
**Requirements**: `PACT-01`, `PACT-02`
**Success criteria:**
1. Every selected action step carries customer-specific current value, target value, delta, unit, and due window.
2. Every step includes a concrete completion criterion and burden or feasibility context instead of abstract advice.
3. Default serialized artifacts expose numeric action contracts while preserving traceability back to underlying technical effects.
4. Regression coverage protects deterministic serialization for representative behavioral, structural, and institutional steps.

### Phase 27: Institution-Aware Decision Intelligence

**Goal**: Attach customer-specific decision-readiness meaning and institution-side dependencies to each personalized plan without breaking the engine-owned contract.
**Depends on**: Phase 26
**Requirements**: `PACT-03`, `DINT-01`, `DINT-02`
**Success criteria:**
1. Customer actions and institution actions are clearly separated but still live inside one ordered plan contract.
2. Each plan can explain how the roadmap changes approval readiness, review posture, or offer eligibility at `4w / 12w / 24w`.
3. Approvals, prerequisite actions, and offer conditions are explicit and safe for product consumption.
4. Institution-aware dependencies stay deterministic and traceable across engine artifacts and downstream consumers.

### Phase 28: Product-Ready Personalized Narratives

**Goal**: Render personalized numeric action plans into clear product narratives for buyer, analyst, and demo surfaces without UI-side reinterpretation.
**Depends on**: Phase 27
**Requirements**: `NARR-01`, `NARR-02`
**Success criteria:**
1. The engine can explain what to do, why it matters, expected numeric effect, and the consequence of completion or miss for each step.
2. Business-first product surfaces consume the same engine-owned contract and keep numeric or technical detail available on demand.
3. Representative personalized plans are understandable without exposing raw engine-native delta language.
4. UI consumers render personalized plans without inventing their own decision logic or narrative meaning.

### Phase 29: Portfolio Validation For Personalized Action Intelligence

**Goal**: Validate the personalized planning layer across the portfolio and compare it against the shipped `v1.3` baseline on specificity, realism, and decision usefulness.
**Depends on**: Phase 28
**Requirements**: `PVAL-01`, `PVAL-02`
**Success criteria:**
1. Portfolio artifacts quantify coverage, realism, and outcome distribution for personalized numeric plans.
2. Proof artifacts compare the personalized-action layer against the `v1.3` baseline on customer specificity, decision clarity, and institution awareness.
3. Supporting evidence shows where personalization improves usefulness and where it remains mixed or narrow.
4. Product confidence surfaces can tell an honest “is this more useful?” story without hiding weaker segments or tradeoffs.

### Why This Milestone Exists

- `v1.3` proved that the engine can be trusted and surfaced cleanly, but many plans still read like transformed model outputs rather than truly customer-specific action contracts.
- The next leverage point is not more generic proof or more website breadth; it is sharper personalized planning intelligence that connects action steps to concrete customer outcomes and institution decisions.
- Portfolio validation now needs to judge whether personalization makes plans more specific and more decision-useful, not just whether the recourse stack still works in aggregate.

### Success Bar

- Personalized plans are numeric, feasible, and customer-specific rather than generic recourse summaries
- Institution-side actions, approvals, and dependencies are explicit in the same plan contract
- Product surfaces can explain personalized plans without adding UI-side interpretation
- Portfolio proof can say whether the personalized planning layer is actually more useful than the shipped `v1.3` baseline

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
| 22. Business-First Demo Center Refactor | v1.3 | 4/4 | Complete | 2026-03-20 |
| 23. Proof & Investor Narrative Hardening | v1.3 | 3/3 | Complete | 2026-03-20 |
| 24. Analyst Workflow & UAT Validation | v1.3 | 3/3 | Complete | 2026-03-20 |
| 25. Pilot Readiness & Demo Ops Baseline | v1.3 | 3/3 | Complete | 2026-03-20 |
| 26. Personalized Numeric Action Contracts | v2.0 | roadmap defined | Planned | - |
| 27. Institution-Aware Decision Intelligence | v2.0 | roadmap defined | Planned | - |
| 28. Product-Ready Personalized Narratives | v2.0 | roadmap defined | Planned | - |
| 29. Portfolio Validation For Personalized Action Intelligence | v2.0 | roadmap defined | Planned | - |
