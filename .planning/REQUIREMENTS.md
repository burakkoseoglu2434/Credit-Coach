# Requirements: Credit Coach

**Defined:** 2026-04-05
**Core Value:** Generate customer-specific credit action plans that are actionable, behaviorally realistic, governance-safe, and measurably useful enough to improve denied-customer outcomes without breaking enterprise trust.

## v1 Requirements

Requirements for milestone `v2.5 Recoverable Customer Targeting & Movement Optimization`. Each maps to exactly one roadmap phase.

### Recoverability Signals

- [ ] **RECV-01**: System computes `approval_gap` for each evaluated customer as deterministic distance from current score to approval threshold.
- [ ] **RECV-02**: System computes `normalized_gap` and `recoverability_score` using existing shipped scores and signals only, with no model retraining.
- [ ] **RECV-03**: System assigns `risk_band` and `recoverability_bucket` (`near_threshold`, `mid_risk`, `structural_limited`) deterministically for each evaluated customer.
- [ ] **RECV-04**: Recoverability signal fields are emitted into evaluation artifacts so cohort analysis can audit them directly.

### Recoverable Classification

- [x] **CLSF-01**: System marks `recoverable_flag=true` only when approval gap is within the defined band, at least one valid recourse path exists, and structural blockers do not dominate.
- [x] **CLSF-02**: System emits `recoverable_reason_codes` explaining why a customer is or is not recoverable.
- [x] **CLSF-03**: Recoverable classification remains explainable and deterministic across reruns.

### Recourse Gating

- [ ] **GATE-01**: Recoverable customers enter `recourse_mode=full` and receive the full multi-path recourse pipeline.
- [ ] **GATE-02**: Non-recoverable customers enter `recourse_mode=limited` and avoid aggressive low-yield action generation.
- [ ] **GATE-03**: Gating does not break planner validity, winner-selection, or trust contracts inherited from `v2.2` and `v2.4`.

### Movement Ranking

- [ ] **MOVE-01**: Planner emits `movement_score` that favors threshold progress, feasibility, and action simplicity.
- [ ] **MOVE-02**: Planner emits heuristic `threshold_reach_probability` for selected or ranked paths.
- [ ] **MOVE-03**: Movement-aware ranking does not introduce invalid winners or trust regressions.

### Targeted Evaluation

- [ ] **EVAL-01**: Cohort evaluation compares global denied customers against the recoverable-only subset.
- [ ] **EVAL-02**: Evaluation publishes `recoverable_customer_rate`, `movement_rate_recoverable`, `movement_rate_global`, `structural_limited_rate`, `recommendation_mode_distribution`, and `threshold_gap_distribution`.
- [ ] **EVAL-03**: Evaluation explicitly states whether targeting improves movement concentration or not, without assuming uplift.

### Narrative Alignment

- [ ] **NARR-01**: Recoverable customers receive `narrative_type=actionable` with strong, focused next-step messaging.
- [ ] **NARR-02**: Non-recoverable customers receive `narrative_type=informational` with honest structural-limit messaging.
- [ ] **NARR-03**: Customer and demo-facing surfaces distinguish actionable versus informational modes without contradiction.

### Execution & Outcome Realization

- [ ] **REAL-01**: System stores selected-path realization context and selected-action execution events additively, without changing core decision or recommendation logic.
- [ ] **REAL-02**: System publishes deterministic action execution, path realization, realized movement, and observation-coverage artifacts from stored observations.
- [ ] **REAL-03**: System evaluates predicted versus observed realization descriptively across recoverable/full versus limited/control posture, without causal or uplift overclaim.

## v2 Requirements

Deferred until a later milestone.

### Future Optimization

- **FUTR-01**: Revisit model retraining or alternative threshold policy only if deterministic recoverability targeting still fails to create enough movement.
- **FUTR-02**: Consider external institution data or live offer data only after recoverability targeting is proven valuable.
- **FUTR-03**: Consider new action types only after recoverability targeting exhausts the current governed action surface.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Model retraining | This milestone must use existing shipped scores and signals only |
| Threshold policy redesign | `v2.3` already proved bounded threshold tuning was not the immediate lever |
| New action types | The bottleneck is targeting and movement concentration, not action-surface richness |
| External data integration | Keep the milestone evaluation-only and deterministic on current data/assets |
| Broad recommendation expansion for structural users | This milestone should avoid pretending to help customers with no realistic movement path |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| RECV-01 | Phase 61 | Complete |
| RECV-02 | Phase 61 | Complete |
| RECV-03 | Phase 61 | Complete |
| RECV-04 | Phase 61 | Complete |
| CLSF-01 | Phase 62 | Complete |
| CLSF-02 | Phase 62 | Complete |
| CLSF-03 | Phase 62 | Complete |
| GATE-01 | Phase 63 | Pending |
| GATE-02 | Phase 63 | Pending |
| GATE-03 | Phase 63 | Pending |
| MOVE-01 | Phase 64 | Pending |
| MOVE-02 | Phase 64 | Pending |
| MOVE-03 | Phase 64 | Pending |
| EVAL-01 | Phase 65 | Pending |
| EVAL-02 | Phase 65 | Pending |
| EVAL-03 | Phase 65 | Pending |
| NARR-01 | Phase 66 | Pending |
| NARR-02 | Phase 66 | Pending |
| NARR-03 | Phase 66 | Pending |
| REAL-01 | Phase 67 | Pending |
| REAL-02 | Phase 67 | Pending |
| REAL-03 | Phase 67 | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-05*
*Last updated: 2026-04-10 after adding Phase 67 Execution & Outcome Realization requirements*
