# Roadmap: Credit Coach

## Milestones

- 🚧 **v2.5 Recoverable Customer Targeting & Movement Optimization** - Phases 61-67 (planning started 2026-04-05)
- ✅ **v2.4 Recourse Capability Expansion & Action Semantics** - Phases 54-60 (shipped 2026-04-05; archive: `.planning/milestones/v2.4-ROADMAP.md`)
- ✅ **v2.3 Threshold & Outcome Optimization** - Phases 49-53 (shipped 2026-04-03; archive: `.planning/milestones/v2.3-ROADMAP.md`)
- ✅ **v1.0 Brownfield Baseline** - Phases 1-7 (historical baseline reconstructed from imported docs, shipped 2026-03-10)
- ✅ **v1.1 Fairness Stability & KPI Hardening** - Phases 8-11 (completed 2026-03-15)
- ✅ **v1.2 Recommendation Quality Hardening** - Phases 12-16 (completed 2026-03-16)
- ✅ **v1.3 Portfolio Intelligence & Productization** - Phases 17-25 (completed 2026-03-20)
- ✅ **v2.0 Personalized Action & Decision Intelligence** - Phases 30-39 (completed 2026-03-22)
- ✅ **v2.1 Decision Ownership & Pilot-Ready Trust** - Phases 40-44 (completed 2026-03-23)
- ✅ **v2.2 Winner Integrity & Consumer Consistency** - Phases 45-48 (shipped 2026-04-02; archive: `.planning/milestones/v2.2-ROADMAP.md`)

## Inter-Milestone Carry-Forward

- ✅ **Phase 42.5 Recommendation Validity Layer** - post-v2.1 carry-forward hardening (completed 2026-03-24; code validation passed, and large-sample reruns now execute locally via deterministic sample-CSV fallback while processed-data-specific reruns still depend on `credit-coach/data/processed/test.parquet`)

## Active Milestone

### 🚧 v2.5 Recoverable Customer Targeting & Movement Optimization (Phases 61-67)

**Goal:** Identify realistically recoverable denied customers, focus full recourse generation on them, and keep structurally limited customers in an honest limited-guidance mode.

**Acceptance checks:**
- recoverable customers are deterministically identified from shipped scores and path evidence
- movement rate in the recoverable cohort is materially higher than the global denied baseline
- structurally limited customers do not receive fake high-yield multi-path treatment
- realized execution and outcome evidence are published without causal overclaim
- `selected_invalid_winner_count = 0`
- no selected-surface drift
- no operator packet contradictions

**Planned phases:**
- Phase 61: Recoverability Signal Definition
- Phase 62: Recoverable Customer Classifier
- Phase 63: Recourse Gating By Recoverability
- Phase 64: Movement-Focused Path Ranking
- Phase 65: Targeted Cohort Evaluation
- Phase 66: Demo & Narrative Alignment
- Phase 67: Execution & Outcome Realization

**Phase details:**

**Phase 61: Recoverability Signal Definition**
Goal: derive deterministic recoverability fields from current score distance and shipped structural signals.
Requirements: `RECV-01`, `RECV-02`, `RECV-03`, `RECV-04`
Success criteria:
- `approval_gap` is emitted per customer from current score vs threshold
- `normalized_gap` and `recoverability_score` are deterministic and explainable
- `risk_band` and `recoverability_bucket` classify customers into `near_threshold`, `mid_risk`, or `structural_limited`
- the new fields appear in customer and cohort evaluation artifacts without model retraining

**Phase 62: Recoverable Customer Classifier**
Goal: turn recoverability signals and path evidence into an explicit recoverable customer decision.
Requirements: `CLSF-01`, `CLSF-02`, `CLSF-03`
Success criteria:
- `recoverable_flag` is true only when approval gap, valid-path existence, and structural-limit checks all pass
- `recoverable_reason_codes` explain positive and negative outcomes
- reruns remain deterministic for the same inputs

**Phase 63: Recourse Gating By Recoverability**
Goal: use recoverability to decide whether each customer receives full recourse or limited informational mode.
Requirements: `GATE-01`, `GATE-02`, `GATE-03`
Success criteria:
- recoverable customers enter `recourse_mode=full`
- non-recoverable customers enter `recourse_mode=limited`
- limited mode avoids aggressive low-yield path generation while preserving trust and planner validity contracts

**Phase 64: Movement-Focused Path Ranking**
Goal: rank plans for realistic progress toward threshold instead of generic best-plan selection alone.
Requirements: `MOVE-01`, `MOVE-02`, `MOVE-03`
Success criteria:
- `movement_score` favors threshold progress, feasibility, and simpler action sets
- heuristic `threshold_reach_probability` is emitted for ranked or selected paths
- ranking changes preserve valid winner selection and do not regress trust counters

**Phase 65: Targeted Cohort Evaluation**
Goal: prove whether recoverability targeting improves movement concentration relative to the global denied baseline.
Requirements: `EVAL-01`, `EVAL-02`, `EVAL-03`
Success criteria:
- cohort evaluation compares global denied vs recoverable-only populations
- required metrics are published, including movement, recommendation mode, and threshold-gap distributions
- the report explicitly distinguishes capability concentration from business uplift claims

**Phase 66: Demo & Narrative Alignment**
Goal: make recoverable vs structural-limited outcomes visible and honest in narratives and demo surfaces.
Requirements: `NARR-01`, `NARR-02`, `NARR-03`
Success criteria:
- recoverable customers get `narrative_type=actionable`
- non-recoverable customers get `narrative_type=informational`
- customer and demo-facing artifacts stay aligned with recoverability and recourse mode decisions

**Phase 67: Execution & Outcome Realization**
Goal: measure whether selected-path recommendations are actually executed and whether they produce observed downstream movement.
Requirements: `REAL-01`, `REAL-02`, `REAL-03`
Success criteria:
- selected-path execution events and realization context are stored additively without changing decision logic
- machine-readable artifacts publish action execution, path realization, and realized-outcome metrics
- final reporting compares predicted versus observed realization descriptively, without causal or business-uplift overclaim

<details>
<summary>✅ v2.4 Recourse Capability Expansion & Action Semantics (Phases 54-60) - SHIPPED 2026-04-05</summary>

Historical archive: `.planning/milestones/v2.4-ROADMAP.md`

- Phase 54: Action Semantics Taxonomy
- Phase 55: Feature → Action Mapping
- Phase 56: DICE Action Space Expansion
- Phase 57: Heuristic / Institution Action Lane
- Phase 58: Multi-Path Recourse Generation
- Phase 59: Action Semantics Rendering
- Phase 60: Validation & Cohort Evaluation

</details>

<details>
<summary>✅ v2.3 Threshold & Outcome Optimization (Phases 49-53) - SHIPPED 2026-04-03</summary>

Historical archive: `.planning/milestones/v2.3-ROADMAP.md`

- Phase 49: Threshold Policy Evaluation & Provenance
- Phase 50: Offer & Readiness Outcome Rules
- Phase 51: Funnel Movement Guardrails & Evidence
- Phase 52: Preferred Policy Baseline & Demo Proof
- Phase 53: Formal Phase 52 Verification

</details>

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

<details>
<summary>✅ v2.0 Personalized Action & Decision Intelligence (Phases 30-39) - SHIPPED 2026-03-22</summary>

Historical archive: `.planning/milestones/v2.0-ROADMAP.md`

- Phase 30: Action Semantics Hardening
- Phase 31: Numeric Target Engine
- Phase 32: Feasibility & Constraint Engine
- Phase 33: Action Difficulty & Execution Modeling
- Phase 34: Offer Layer Integration
- Phase 35: Narrative Generation v2
- Phase 36: Product Surface Upgrade
- Phase 37: Portfolio-Level Numeric Impact
- Phase 38: Calibration & Validation
- Phase 39: Pilot Integration

</details>

<details>
<summary>✅ v2.1 Decision Ownership & Pilot-Ready Trust (Phases 40-44) - SHIPPED 2026-03-23</summary>

Historical archive: `.planning/milestones/v2.1-ROADMAP.md`

- Phase 40: Contract & Trust Repair
- Phase 40.5: Decision Ownership Layer
- Phase 41: Cohort & Decision Calibration
- Phase 43: Operator Review Pack
- Phase 42: Planner Quality & Source Mix
- Phase 44: Production Pilot Baseline
- Post-shipment carry-forward: Phase 42.5 Recommendation Validity Layer (completed 2026-03-24)

</details>

<details>
<summary>✅ v2.2 Winner Integrity & Consumer Consistency (Phases 45-48) - SHIPPED 2026-04-02</summary>

Historical archive: `.planning/milestones/v2.2-ROADMAP.md`

- Phase 45: Winner Integrity Hard Stop
- Phase 46: Dice Lane Validity Enforcement
- Phase 47: Selected Surface Consistency
- Phase 48: Operator Packet Coherence

</details>

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
| 39. Pilot Integration | v2.0 | 3/3 | Complete | 2026-03-22 |
| 40. Contract & Trust Repair | v2.1 | 3/3 | Complete | 2026-03-23 |
| 40.5 Decision Ownership Layer | v2.1 | 3/3 | Complete | 2026-03-23 |
| 41. Cohort & Decision Calibration | v2.1 | 3/3 | Complete | 2026-03-23 |
| 43. Operator Review Pack | v2.1 | 3/3 | Complete | 2026-03-23 |
| 42. Planner Quality & Source Mix | v2.1 | 3/3 | Complete | 2026-03-23 |
| 42.5 Recommendation Validity Layer | carry-forward | 3/3 | Complete | 2026-03-24 |
| 44. Production Pilot Baseline | v2.1 | 3/3 | Complete | 2026-03-23 |
| 45. Winner Integrity Hard Stop | v2.2 | 3/3 | Complete | 2026-03-26 |
| 46. Dice Lane Validity Enforcement | v2.2 | 3/3 | Complete | 2026-03-26 |
| 47. Selected Surface Consistency | v2.2 | 3/3 | Complete | 2026-04-01 |
| 48. Operator Packet Coherence | v2.2 | 3/3 | Complete | 2026-04-02 |
| 49. Threshold Policy Evaluation & Provenance | v2.3 | 3/3 | Complete | 2026-04-02 |
| 50. Offer & Readiness Outcome Rules | v2.3 | 3/3 | Complete | 2026-04-03 |
| 51. Funnel Movement Guardrails & Evidence | v2.3 | 3/3 | Complete | 2026-04-03 |
| 52. Preferred Policy Baseline & Demo Proof | v2.3 | 3/3 | Complete | 2026-04-03 |
| 53. Formal Phase 52 Verification | v2.3 | 1/1 | Complete | 2026-04-03 |
| 54. Action Semantics Taxonomy | v2.4 | 1/1 | Complete    | 2026-04-03 |
| 55. Feature → Action Mapping | v2.4 | 3/3 | Complete | 2026-04-04 |
| 56. DICE Action Space Expansion | v2.4 | 3/3 | Complete | 2026-04-04 |
| 57. Heuristic / Institution Action Lane | v2.4 | 3/3 | Complete | 2026-04-04 |
| 58. Multi-Path Recourse Generation | v2.4 | 3/3 | Complete | 2026-04-04 |
| 59. Action Semantics Rendering | v2.4 | 3/3 | Complete | 2026-04-04 |
| 60. Validation & Cohort Evaluation | v2.4 | 3/3 | Complete | 2026-04-05 |
| 61. Recoverability Signal Definition | v2.5 | 3/3 | Complete | 2026-04-06 |
| 62. Recoverable Customer Classifier | v2.5 | 3/3 | Complete | 2026-04-07 |
| 63. Recourse Gating By Recoverability | v2.5 | 3/3 | Complete | 2026-04-07 |
| 64. Movement-Focused Path Ranking | v2.5 | 3/3 | Complete | 2026-04-08 |
| 65. Targeted Cohort Evaluation | v2.5 | 3/3 | Complete | 2026-04-10 |
| 66. Demo & Narrative Alignment | v2.5 | 0/0 | Planned | — |
| 67. Execution & Outcome Realization | v2.5 | 1/3 | In Progress | 2026-04-10 |
