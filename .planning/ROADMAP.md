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
**Phases**: 30-39 currently defined
**Status**: Active; Phases 30-38 complete and Phase 39 is planned and ready for execution

### Phase 30: Action Semantics Hardening

**Goal**: Turn feature deltas into a stable real-world action mapping layer that is deterministic, typed, and product-safe.
**Depends on**: Phase 25
**Requirements**: `ACT-01`
**Success criteria:**
1. Feature-level changes map deterministically to action types, action groups, and user-facing action keys.
2. Composite and grouped actions remain traceable back to technical effects without leaking raw feature language into default outputs.
3. Regression coverage protects action-semantic stability across representative behavioral, structural, and institutional cases.

### Phase 31: Numeric Target Engine

**Goal**: Convert action semantics into customer-specific numeric targets with explicit units, deltas, and time windows.
**Depends on**: Phase 30
**Requirements**: `NUM-01`
**Success criteria:**
1. Each selected action step carries current value, target value, delta, unit, and due horizon.
2. Numeric targets are customer-specific rather than template-only defaults.
3. Numeric target serialization stays deterministic and auditable across the engine contract.

### Phase 32: Feasibility & Constraint Engine

**Goal**: Ensure numeric targets are realistic, repairable when safe, and rejected when infeasible.
**Depends on**: Phase 31
**Requirements**: `FEAS-01`
**Success criteria:**
1. Numeric targets pass through explicit clip, repair, reject, and dependency rules before they become valid steps.
2. Feasibility logic explains why a target is valid, repaired, or rejected.
3. Unrealistic numeric recommendations cannot surface as normal valid winners.

### Phase 33: Action Difficulty & Execution Modeling

**Goal**: Strengthen the difficulty and follow-through profile of each action so realistic completion becomes part of plan quality.
**Depends on**: Phase 32
**Requirements**: `EXEC-01`
**Success criteria:**
1. Every action carries a measurable difficulty or execution-likelihood profile.
2. Harder or longer-horizon steps are penalized in realistic plan quality rather than treated like neutral targets.
3. The engine can distinguish nominally strong but execution-weak plans from realistically executable ones.

### Phase 34: Offer Layer Integration

**Goal**: Make institution actions explicit through a separate offer layer with terms, approvals, and dependencies.
**Depends on**: Phase 33
**Requirements**: `OFFR-01`
**Success criteria:**
1. Institution-side actions are represented as explicit offers instead of being mixed indistinguishably with customer actions.
2. Offer terms, approval state, and dependencies are machine-readable and product-safe.
3. Customer and institution steps can coexist in one plan without collapsing their semantics.

### Phase 35: Narrative Generation v2

**Goal**: Translate numeric and institution-aware plans into clear product narratives while preserving traceability.
**Depends on**: Phase 34
**Requirements**: `NARV-01`
**Success criteria:**
1. Narratives explain what to do, why it matters, expected numeric effect, and consequence of completion or miss.
2. Numeric and offer-aware plan meaning comes from the engine contract rather than UI-side invention.
3. Default language is business-first while numeric and technical detail remain available on demand.

### Phase 36: Product Surface Upgrade

**Goal**: Bring the new numeric personalized plans into demo and product surfaces through typed artifact consumption.
**Depends on**: Phase 35
**Requirements**: `SURF-01`
**Success criteria:**
1. Demo and product surfaces render personalized numeric plans directly from engine-owned artifacts.
2. UI layers do not re-interpret plan meaning or invent new decision logic.
3. Numeric, institution-aware, and narrative layers remain coherent across product surfaces.

### Phase 37: Portfolio-Level Numeric Impact

**Goal**: Measure the portfolio-wide distribution and impact of the personalized numeric action layer.
**Depends on**: Phase 36
**Requirements**: `PVAL-01`
**Success criteria:**
1. Portfolio artifacts quantify how often personalized numeric plans exist, what they recommend, and how their impact distributes across segments.
2. Portfolio views surface where numeric personalization improves usefulness and where it remains narrow or weak.
3. Product-facing proof can speak about personalized-action impact beyond single-case demos.

### Phase 38: Calibration & Validation

**Goal**: Validate that numeric recommendations and impact distributions are realistic, calibrated, and not falsely optimistic.
**Depends on**: Phase 37
**Requirements**: `CAL-01`
**Success criteria:**
1. Numeric targets and impact distributions are checked for realism and calibration drift.
2. False optimism and unstable target ranges are surfaced explicitly in validation outputs.
3. The personalized numeric layer can be trusted as a controlled recommendation surface rather than a speculative generator.

### Phase 39: Pilot Integration

**Goal**: Start the personalized planning loop against real institution-style data and pilot integration seams.
**Depends on**: Phase 38
**Requirements**: `PILT-01`
**Success criteria:**
1. The personalized planning loop can run through pilot-style input and output contracts without breaking engine-owned truth.
2. Real institution data seams are explicit enough to support pilot onboarding and evaluation.
3. The system can start a learning loop from pilot integration rather than staying purely milestone-local and synthetic.

### Why This Milestone Exists

- `v1.3` proved the engine and surfaces can be trusted, but many outputs still stop at model-native recourse rather than truly personalized action intelligence.
- The next milestone needs a deeper stack than a four-phase pass: semantics, numeric targeting, feasibility, execution realism, offer integration, narrative generation, product consumption, portfolio impact, calibration, and pilot integration all need explicit closure.
- Portfolio validation now needs to answer not just whether plans work, but whether customer-specific numeric plans are realistic, interpretable, and institution-usable.

### Success Bar

- Feature deltas become real actions before they become numeric targets
- Personalized plans are numeric, feasible, and customer-specific rather than generic recourse summaries
- Institution-side actions, approvals, and dependencies are explicit in the same plan contract
- Product surfaces can explain personalized plans without adding UI-side interpretation
- Portfolio proof can say whether the personalized planning layer is actually more useful than the shipped `v1.3` baseline
- Calibration and pilot integration confirm the new layer is realistic enough to carry into institution workflows

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
| 30. Action Semantics Hardening | v2.0 | 3/3 | Complete | 2026-03-20 |
| 31. Numeric Target Engine | v2.0 | 3/3 | Complete | 2026-03-21 |
| 32. Feasibility & Constraint Engine | v2.0 | 3/3 | Complete | 2026-03-21 |
| 33. Action Difficulty & Execution Modeling | v2.0 | 3/3 | Complete | 2026-03-21 |
| 34. Offer Layer Integration | v2.0 | 3/3 | Complete | 2026-03-22 |
| 35. Narrative Generation v2 | v2.0 | 3/3 | Complete | 2026-03-22 |
| 36. Product Surface Upgrade | v2.0 | 3/3 | Complete | 2026-03-22 |
| 37. Portfolio-Level Numeric Impact | v2.0 | 3/3 | Complete | 2026-03-22 |
| 38. Calibration & Validation | v2.0 | 3/3 | Complete | 2026-03-22 |
| 39. Pilot Integration | v2.0 | roadmap defined | Planned | - |
