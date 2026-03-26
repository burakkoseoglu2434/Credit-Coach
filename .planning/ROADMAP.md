# Roadmap: Credit Coach

## Milestones

- ✅ **v1.0 Brownfield Baseline** - Phases 1-7 (historical baseline reconstructed from imported docs, shipped 2026-03-10)
- ✅ **v1.1 Fairness Stability & KPI Hardening** - Phases 8-11 (completed 2026-03-15)
- ✅ **v1.2 Recommendation Quality Hardening** - Phases 12-16 (completed 2026-03-16)
- ✅ **v1.3 Portfolio Intelligence & Productization** - Phases 17-25 (completed 2026-03-20)
- ✅ **v2.0 Personalized Action & Decision Intelligence** - Phases 30-39 (completed 2026-03-22)
- ✅ **v2.1 Decision Ownership & Pilot-Ready Trust** - Phases 40-44 (completed 2026-03-23)
- 🟡 **v2.2 Winner Integrity & Consumer Consistency** - Phases 45-48 (active; started 2026-03-24)

## Inter-Milestone Carry-Forward

- ✅ **Phase 42.5 Recommendation Validity Layer** - post-v2.1 carry-forward hardening (completed 2026-03-24; code validation passed, and large-sample reruns now execute locally via deterministic sample-CSV fallback while processed-data-specific reruns still depend on `credit-coach/data/processed/test.parquet`)

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

## Active Milestone: v2.2 Winner Integrity & Consumer Consistency

**Problem statement**

Large-sample reruns and targeted failure analysis showed that selected invalid recommendation leakage is now the dominant trust gap:
- invalid candidates are filtered in `choose_best_plan(...)`, but if the filtered preferred set becomes empty the planner falls back to the original invalid pool
- all leaked selected invalid winners were `dice` winners
- validity annotation itself appears correct
- consumer surfaces remain inconsistent in several cases: invalid selected actions can still appear in operator short view, some external `CONDITIONAL` cases still point at selected `REJECTED` rows, and approved packets can still show fallback blockers

**North star**

No invalid recommendation can ever become the selected winner or leak into selected consumer surfaces. `dice` and internal lanes must obey the same validity rules, and selected plan rows, decision summaries, operator packets, and explanation packs must tell one coherent story.

**Main phases / workstreams**

| Phase | Workstream | Goal | Requirements | Success Criteria |
|-------|------------|------|--------------|------------------|
| 45 | Winner Integrity Hard Stop | Remove the planner fallback path that revives invalid candidates and make selected validity truth explicit | WINT-01, WINT-02, WINT-03 | 3 |
| 46 | Dice Lane Validity Enforcement | Enforce typed parity, lane-quality eligibility, and DICE-specific proof before planner selection | DICE-01, DICE-02 | 3 |
| 47 | Selected Surface Consistency | Align selected plan rows, decision summaries, collection metrics, and explanation outputs around one selected winner | CONS-01, CONS-02, CONS-03 | 3 |
| 48 | Operator Packet Coherence | Remove contradictory blockers and invalid short-view actions while preserving diagnostics | OPER-01, OPER-02, OPER-03 | 3 |

### Phase Details

**Phase 45: Winner Integrity Hard Stop**
Goal: remove the planner fallback path that resurrects invalid candidates after validity filtering and make selected validity truth explicit in raw and flat artifacts.
Requirements: `WINT-01`, `WINT-02`, `WINT-03`
Success criteria:
1. Validity filtering can collapse a preferred candidate subset without reviving the original invalid pool.
2. Large-sample reruns show zero selected winners with `recommendation_validity_status = invalid`.
3. Selected raw and flat artifacts carry winning-plan validity and provenance consistently.

**Phase 46: Dice Lane Validity Enforcement**
Goal: make `dice` candidates obey the same validity gates and fallback discipline as internal plans.
Requirements: `DICE-01`, `DICE-02`
Success criteria:
1. `dice` candidates carry action-level and plan-level validity fields before ranking and winner selection.
2. Invalid `dice` candidates remain visible in diagnostics but cannot be emitted as selected winners.
3. Rerun diagnostics distinguish invalid `dice` leakage from valid-but-unselected `dice` alternatives cleanly.

**Phase 47: Selected Surface Consistency**
Goal: align selected plan rows, external decision summaries, collection metrics, and explanation surfaces around one selected winner.
Requirements: `CONS-01`, `CONS-02`, `CONS-03`
Success criteria:
1. No external `CONDITIONAL` output points at a selected plan row whose plan status is `REJECTED`.
2. `best_plan_id`, selected plan rows, and collection metrics agree for every sampled customer in rerun audits.
3. Operator and explanation surfaces render recommendation text from the selected valid winner only.

**Phase 48: Operator Packet Coherence**
Goal: remove contradictory blockers and invalid short-view actions from operator packets without hiding legitimate warning diagnostics.
Requirements: `OPER-01`, `OPER-02`, `OPER-03`
Success criteria:
1. Operator short view never renders invalid selected actions as recommended next actions.
2. Approved packets with zero active drivers render no fallback blockers.
3. Warning badges and appendix diagnostics stay available without contradicting short-view guidance.

**Acceptance criteria**

- `pilot_mixed`, `risk_band_balanced`, and `offer_needed_balanced` reruns show `0` selected winners with `recommendation_validity_status = invalid`.
- All selected `dice` winners satisfy the same hard validity gate as internal winners.
- `0` external `CONDITIONAL` outputs point at selected `REJECTED` plan rows.
- `0` approved packets with zero active drivers show fallback blockers.
- `0` operator short views render invalid selected actions as the chosen recommendation.

**Out of scope**

- threshold widening or approval-rate optimization
- redesign of Phases `40`, `40.5`, `41`, `42`, `42.5`, or `43`
- new borrower-facing channels, live institution integrations, or compliance automation

**Recommended implementation order**

1. Phase `45` — stop invalid winner leakage at the planner boundary
2. Phase `46` — make the `dice` lane obey the same validity contract end-to-end
3. Phase `47` — align selected-surface truth across raw, flat, and explanation outputs
4. Phase `48` — clean up operator packet coherence once selected truth is stable

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
| 47. Selected Surface Consistency | v2.2 | 0/3 | Planned | — |
| 48. Operator Packet Coherence | v2.2 | 0/3 | Planned | — |
