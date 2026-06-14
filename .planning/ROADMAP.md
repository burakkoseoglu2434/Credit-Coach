# Roadmap: Credit Coach

## Milestones

- 🚧 **v2.7 Coverage Expansion & Action Surface Unlock** - Phases 71-77 (planning started 2026-04-14)
- ✅ **v2.6 Real Cohort Evidence & Realization Proof** - Phase 68 (shipped 2026-04-11)
- ✅ **v2.5 Recoverable Customer Targeting & Movement Optimization** - Phases 61-67 (foundation validated by v2.6 evidence run)
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
- ○ **Phase 69: Evidence Amplification** - retained as post-v2.6 evidence backlog while v2.7 becomes the active milestone
- ○ **Phase 70: Full Lending Club Dataset Validation** - retained as validation backlog / carry-forward work; phase numbering for v2.7 continues from 71

## Active Milestone

### 🚧 v2.7 Coverage Expansion & Action Surface Unlock (Phases 71-77)

**Goal:** Expand actionable recommendation coverage beyond the current narrow recoverable slice and unlock multi-action, multi-step recommendation surfaces without breaking trust, validity, or consistency guarantees.

**Why this milestone exists:**
- v2.5 and v2.6 proved that recoverability gating and trust contracts work correctly
- W2a results show only about `~3%` of customers receive actionable recommendations, with about `~97%` in empty-state limited mode
- surfaced recommendations are overly concentrated in a single action type
- internal planner generates diverse multi-path strategies, but the product surface does not expose that richness
- the system is currently algorithmically strong but product-surface limited

**Acceptance checks:**
- actionable coverage increases from `~3%` to at least `10-20%`
- mid-risk customers achieve non-zero actionable coverage
- surfaced recommendations include multiple action types, with no single action type above `50%` dominance
- multi-step or sequential plans are surfaced where applicable
- overall median `movement_score` remains above `0`
- `selected_invalid_winner_count = 0`
- `selected_surface_drift_count = 0`
- `operator_packet_contradiction_count = 0`

**Planned phases:**
- Phase 71: Coverage Diagnostics & Failure Analysis
- Phase 72: Recoverability Gate Relaxation (Controlled)
- Phase 73: Action Surface Expansion
- Phase 74: Multi-Step Plan Surfacing
- Phase 75: Mid-Risk Segment Unlock
- Phase 76: Performance & Artifact Optimization
- Phase 77: Cohort Rerun & Comparative Evaluation

**Phase details:**

**Phase 71: Coverage Diagnostics & Failure Analysis**
Goal: explain why customers fall into limited mode and publish segment-level failure patterns that quantify the true coverage bottleneck.
Requirements: `COV-01`, `COV-02`, `COV-03`
Success criteria:
- a machine-readable diagnostic artifact explains recommendation-mode outcomes per customer
- failure reasons are broken down across at least `near_threshold`, `mid_risk`, and `hard_denied` segments
- empty-state rate, actionability rate, and winner-selection availability are published overall and by segment

**Phase 72: Recoverability Gate Relaxation (Controlled)**
Goal: introduce a safer intermediate recommendation tier that reduces empty-state overuse without compromising trust contracts.
Requirements: `GATE-01`, `GATE-02`, `GATE-03`, `TRUST-01`, `TRUST-02`, `TRUST-03`
Success criteria:
- an intermediate tier such as `assisted_full` is available for credible but lower-confidence progress recommendations
- relaxed gating still prevents invalid selected winners, surface drift, and operator contradictions
- surfaced output explains why each customer is in `full`, `assisted_full`, or `limited`

**Phase 73: Action Surface Expansion**
Goal: move from single-action surfacing to top-k surfaced actions using already-supported internal action diversity.
Requirements: `SURF-01`, `SURF-02`, `SURF-03`, `TRUST-04`
Success criteria:
- customers can receive more than one surfaced actionable recommendation when multiple valid action families exist
- surfaced recommendations use existing semantics such as refinance, consolidation, restructuring, or loan-amount adjustment where internally available
- cohort artifacts publish action-type distribution metrics and show reduced single-action dominance
Plans: 2 plans
- [ ] 73-01-PLAN.md — top-k=2 secondary action surfacing (full-tier, diversity-first, institutional-excluded) [SURF-01, SURF-02, TRUST-04]
- [ ] 73-02-PLAN.md — action-type distribution cohort metrics + n=500 trust-counter re-run [SURF-03, TRUST-04]

**Phase 74: Multi-Step Plan Surfacing**
Goal: expose sequential or staged plans when honest customer guidance requires order, dependencies, or time-based progression.
Requirements: `STEP-01`, `STEP-02`, `STEP-03`, `TRUST-04`
Success criteria:
- surfaced output can represent ordered multi-step plans instead of only flat single actions
- narratives remain aligned with selected-plan evidence and do not imply unattested approval outcomes
- step ordering remains deterministic and reproducible for the same inputs

**Phase 75: Mid-Risk Segment Unlock**
Goal: bring mid-risk customers into the actionable surface through longer-horizon and partial-progress recommendations.
Requirements: `MID-01`, `MID-02`, `MID-03`, `TRUST-04`
Success criteria:
- mid-risk customers receive non-empty recommendations even when one-step threshold reach is unlikely
- product messaging frames these plans as progress, readiness, or staged improvement rather than implied approval certainty
- evaluation artifacts separately publish mid-risk actionable coverage

**Phase 76: Performance & Artifact Optimization**
Goal: keep broader action surfacing evaluation-feasible and artifact generation reproducible at larger candidate volumes.
Requirements: `PERF-01`, `PERF-02`, `PERF-03`
Success criteria:
- candidate payload size and repeated computations are reduced through caching, reuse, batching, or equivalent optimization
- performance changes do not silently alter recommendation semantics
- artifacts remain reproducible and comparable to the W2a baseline

**Phase 77: Cohort Rerun & Comparative Evaluation**
Goal: rerun the cohort under v2.7 logic and publish a structured comparison against the W2a baseline.
Requirements: `EVAL-01`, `EVAL-02`, `EVAL-03`, `TRUST-01`, `TRUST-02`, `TRUST-03`
Success criteria:
- comparison artifacts report coverage, movement, recommendation-mode mix, and action diversity against W2a
- segment-level outcomes are published for at least `near_threshold`, `mid_risk`, and `hard_denied`
- the final report explicitly states whether trust counters stayed clean and whether milestone targets were achieved

## Recent Prior Milestone & Deferred Backlog

### ✅ v2.6 Real Cohort Evidence & Realization Proof (Phase 68) — SHIPPED 2026-04-11

**Goal:** move from audit-passed capability to evidence-backed reporting by running the canonical denied cohort under the shipped runtime and integrating Phase 67 realized outcomes into an evidence-grade report (descriptive, non-causal).

**Acceptance checks:**
- cohort run uses `dataset_scope=full_processed` and the **full available denied population under shipped runtime** (`n=367`), with sampling metadata recorded (with/without replacement)
- report explicitly publishes recoverable rate, movement rates (recoverable/full vs global denied), and threshold reach possible rate
- Phase 67 realized-outcome artifacts are integrated (or explicitly marked sparse/missing) without causal claims
- investor-ready summary and an explicit “evidence strong / weak” decision are produced with conservative wording

**Planned phases:**
- ✅ Phase 68: Real Cohort Evidence Run (3/3 complete)

**Outcome:**
- Trust counters: clean (`selected_invalid_winner_count=0`, `selected_surface_drift_count=0`, `operator_packet_contradiction_count=0`)
- Final classification: **weak evidence (trust-clean)** (limitations: `recoverable_full_mode n=4`, realized-outcome evidence status `sparse`)

### ○ Phase 69: Evidence Amplification (Planned)

**Goal:** increase evidence strength and observation coverage over the shipped runtime without changing model, thresholds, planner, or recourse logic.

### ○ Phase 70: Full Lending Club Dataset Validation (Planned)

**Goal:** validate the full system end-to-end on the complete Lending Club dataset (~1.3M rows, same locked 48-feature schema) without changing any model, `tau_0`, planner, recourse, or ranking logic.

Requirements: `LCFULL-01`, `LCFULL-02`, `LCFULL-03`, `LCFULL-04`

**Acceptance checks:**
- full dataset is prepared into parquet under a dedicated processed-data root (non-destructive)
- schema remains compatible with the existing 48-feature contract (no feature changes)
- cohort evaluations run at increasing scale (smoke → medium → large) with artifacts captured under `v26_lendingclub_full_*`
- trust counters remain clean (or breakage is detected and reported explicitly)
- Phase 70 report is descriptive, non-causal, and classifies evidence strength as `strong / weak / inconclusive`

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
| 66. Demo & Narrative Alignment | v2.5 | 3/3 | Complete | 2026-04-10 |
| 67. Execution & Outcome Realization | v2.5 | 3/3 | Complete | 2026-04-10 |
| 68. Real Cohort Evidence Run | v2.6 | 3/3 | Complete | 2026-04-11 |
| 69. Evidence Amplification | v2.6 | 3/3 | Complete | 2026-04-11 |
| 70. LendingClub Full Dataset Validation | v2.6 | 0/3 | Not Started (superseded by 71-72) | - |
| 71. Coverage Diagnostics & Failure Analysis | v2.7 | 2/2 | Complete | 2026-04-18 |
| 72. Recoverability Gate Relaxation (Controlled) | v2.7 | 2/2 | Complete | 2026-04-20 |
