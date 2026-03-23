# Roadmap: Credit Coach

## Milestones

- ✅ **v1.0 Brownfield Baseline** - Phases 1-7 (historical baseline reconstructed from imported docs, shipped 2026-03-10)
- ✅ **v1.1 Fairness Stability & KPI Hardening** - Phases 8-11 (completed 2026-03-15)
- ✅ **v1.2 Recommendation Quality Hardening** - Phases 12-16 (completed 2026-03-16)
- ✅ **v1.3 Portfolio Intelligence & Productization** - Phases 17-25 (completed 2026-03-20)
- ✅ **v2.0 Personalized Action & Decision Intelligence** - Phases 30-39 (completed 2026-03-22)
- 🟡 **v2.1 Decision Ownership & Pilot-Ready Trust** - Phases 40-44 (started 2026-03-23)

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

## Active Milestone

### v2.1 Decision Ownership & Pilot-Ready Trust

**Goal:** Transform the system from a decision-intelligence prototype into a deterministic, pilot-ready fintech decision system.

**North Star**
- business-visible decisions: `APPROVED | CONDITIONAL | REJECTED`
- internal decisions: `APPROVED | CONDITIONAL | REJECTED | NEEDS_REVIEW`
- `APPROVED + CONDITIONAL >= 30%`
- `APPROVED >= 10%`
- internal `NEEDS_REVIEW < 10%` target and `< 20%` hard max
- deterministic decision for every customer
- one-line business explanation plus structured drivers
- operator can review 50 customers in under 30 minutes

**Execution order:** `40 -> 40.5 -> 41 -> 43 -> 42 -> 44`

### Phase 40: Contract & Trust Repair

**Goal:** Make raw and flat customer artifacts null-free, parity-safe, and trustworthy enough to carry deterministic decision outcomes.
**Requirements:** `TRST-01`, `TRST-02`
**Tasks:**
- enforce null-free decision-critical fields and checkpoint statuses across `customer_roadmap.json`, flat collection tables, and summary outputs
- add raw-vs-flat parity checks, contract-health flags, and explicit classification for data issues without exposing `NEEDS_REVIEW` externally
- publish contract-health metrics in collection manifest and summary so trust failures become first-class review signals
**Acceptance criteria:**
1. Critical decision fields and checkpoint statuses have `0%` null rate in generated raw and flat artifacts.
2. Raw-vs-flat mismatches are classified and surfaced, and external outputs map inconsistency to safe `CONDITIONAL` data-issue handling instead of leaking internal states.
3. Contract-health counts are visible in collection summary, manifest, and customer-level flat outputs.
**Outputs/Artifacts:**
- null-free `customer_roadmap.json` and flat collection contracts
- parity and contract-health columns in `customer_metrics.csv` plus manifest counters
- expanded `collection_summary.md` contract-health section

### Phase 40.5: Decision Ownership Layer

**Goal:** Add deterministic internal and external decision ownership with ordered policy logic, confidence gating, readiness gating, and safe subtypes.
**Requirements:** `DEC-01`, `DEC-02`, `DEC-03`
**Tasks:**
- add final decision contract fields for business-visible status, internal status, decision confidence, expected readiness, rejection subtype, conditional subtype, one-line reason, numeric drivers, and a numeric driver-aligned upgrade condition
- implement fixed decision ordering `REJECTED -> APPROVED -> CONDITIONAL -> NEEDS_REVIEW` with global zero-step rejection and deterministic gating rules
- ship baseline policy defaults: approval realization `>= 0.50`, expected PD improvement `>= 0.02`, `week_4` readiness plus `4w` gate or strong execution for approval, conditional confidence `>= 0.3`, and internal review below `0.4`
- bind readiness, confidence, and offer maturity to decision logic so internal exceptions stay internal, inactive or provisional offers stay `CONDITIONAL`, and external outputs stay three-state only
**Acceptance criteria:**
1. Every customer receives deterministic internal and business-visible decisions from the same policy version.
2. `step_count == 0` always maps to `REJECTED` with `rejection_type = NO_PATH`.
3. `decision_confidence < 0.4` maps to internal `NEEDS_REVIEW`, while business-visible outputs remain in `APPROVED | CONDITIONAL | REJECTED`.
4. `expected_readiness` in `week_12` or `week_24` can never be externally `APPROVED`.
5. Inactive and provisional offers can only yield `CONDITIONAL`, while `APPROVED` remains limited to nonzero-step paths with active, rankable support or no offer gate.
**Outputs/Artifacts:**
- decision-policy fields in customer roadmap and flat collection outputs
- deterministic subtype taxonomy for `rejection_type` and `conditional_type`
- policy-versioned decision explanations with numeric drivers and upgrade conditions

### Phase 41: Cohort & Decision Calibration

**Goal:** Evaluate and tune deterministic decision policy across mixed and stress-test cohorts instead of only denied-heavy inspection runs.
**Requirements:** `CAL-01`, `CAL-02`
**Tasks:**
- add mixed and balanced cohort policies alongside `denied_first_near`, including pilot-ready funnel sampling
- produce approve, conditional, rejected, and internal-review funnel metrics plus readiness distribution for each cohort
- add threshold-tuning outputs that compare policy versions, confidence thresholds, and false-positive proxies against North Star targets
**Acceptance criteria:**
1. Collection runs can emit decision funnels for both stress-test and mixed pilot cohorts.
2. Policy-version comparison artifacts show approve rate, conditional rate, rejected rate, internal review rate, and readiness distribution.
3. Calibration outputs quantify whether thresholds meet `APPROVED + CONDITIONAL >= 30%` and `APPROVED >= 10%` targets on the chosen pilot cohort.
**Outputs/Artifacts:**
- cohort-aware collection manifest and selection metadata
- decision-funnel and policy-comparison sections in `collection_summary.md`
- threshold-tuning and calibration review artifacts for pilot cohorts

### Phase 43: Operator Review Pack

**Goal:** Turn collection runs into short, operator-usable decision packs that support 50-customer review in under 30 minutes.
**Requirements:** `OPS-01`, `OPS-02`
**Tasks:**
- generate per-customer operator packets with final decision, one-line reason, numeric drivers, expected readiness, downside risk, blockers, offer state, and upgrade condition
- add pilot-review summary sections for dominant rejection reasons, conditional hot spots, offer dependency, and contract health
- keep technical traces available behind operator-safe summaries instead of mixing both layers together
**Acceptance criteria:**
1. A reviewer can scan 50 customer packets from one run without opening raw technical artifacts by default.
2. Every non-approved customer packet explains why the decision is not approved yet and what would upgrade it.
3. Collection summary surfaces dominant rejection and conditional patterns in operator language plus supporting technical anchors.
**Outputs/Artifacts:**
- operator review packet artifact set for each collection run
- operator-oriented summary blocks in `collection_summary.md`
- customer-level decision packet fields in flat review outputs

### Phase 42: Planner Quality & Source Mix

**Goal:** Remove empty winners, expose source mix honestly, and make internal planner quality more competitive with external candidate sources.
**Requirements:** `PLAN-01`
**Tasks:**
- prevent zero-action or semantically empty plans from winning or surviving as best outcomes
- add explicit source-mix reporting for `internal`, `dice`, `rule`, and `fallback` candidates across customer and cohort outputs
- improve internal planner competitiveness while preserving deterministic decision policy and contract truth
**Acceptance criteria:**
1. Zero-action best plans disappear from decision outcomes and are rejected before final decision packaging.
2. Source-mix metrics are visible in collection summary and customer-level plan outputs.
3. Internal planner wins a measurable non-zero share of best-plan selections on calibration cohorts.
**Outputs/Artifacts:**
- best-plan source-mix metrics in flat outputs and summaries
- contender filtering rules that reject empty winners before decision finalization
- planner-quality review artifacts linked to cohort calibration results

### Phase 44: Production Pilot Baseline

**Goal:** Package deterministic decision ownership into a rerunnable, versioned, pilot-ready operating baseline.
**Requirements:** `PROD-01`, `PROD-02`
**Tasks:**
- add policy-versioned rerun, artifact QA, and pilot refresh workflow for decision outputs
- compare `v2.0` versus `v2.1` decision outcomes in pilot summaries and policy-review docs
- publish institution-facing explanation and pilot docs that expose only business-visible decisions and safe reasons
**Acceptance criteria:**
1. One pilot workflow can rerun deterministic decision artifacts with QA and policy-version comparison.
2. Institution-facing docs never expose internal `NEEDS_REVIEW` while still explaining `APPROVED`, `CONDITIONAL`, and `REJECTED` outcomes.
3. Pilot summaries show version-to-version changes in approve rate, conditional rate, and rejection composition.
**Outputs/Artifacts:**
- pilot decision QA and refresh workflow outputs
- policy-version comparison report for `v2.0` versus `v2.1`
- institution-facing pilot and explanation documentation

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
| 42. Planner Quality & Source Mix | v2.1 | 0/3 | Planned | — |
| 44. Production Pilot Baseline | v2.1 | 0/3 | Planned | — |
