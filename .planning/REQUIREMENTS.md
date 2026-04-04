# Requirements: Credit Coach

**Defined:** 2026-04-03
**Core Value:** Generate customer-specific credit action plans that are actionable, behaviorally realistic, governance-safe, and measurably useful enough to improve denied-customer outcomes without breaking enterprise trust.

## v1 Requirements

### Action Semantics Taxonomy
- [x] **SEM-01**: Define canonical action categories: utilization, burden reduction, delinquency cleanup, verification, restructuring, application flexing, institution relief
- [x] **SEM-02**: Add action_owner field (customer, institution, hybrid)
- [x] **SEM-03**: Verify all existing actions map into the taxonomy with zero unclassified leftovers

### Feature Mapping
- [x] **MAP-01**: Map the 48 features into actionable transformations
- [x] **MAP-02**: Add action_type, numeric_target_required, and institution_required fields
- [x] **MAP-03**: Achieve ≥ 80% coverage mapped to at least one action

### DICE Space Expansion
- [x] **DICE-01**: Expand DICE to support loan_amnt, installment, term
- [x] **DICE-02**: Expand DICE to support selected delinquency and verification_status features
- [x] **DICE-03**: Ensure Phase 46 gates hold (annotation completeness, semantic quality, contender eligibility)
- [x] **DICE-04**: Maintain valid diversity and winner integrity without regression

### Heuristic / Institution Action Lane
- [x] **INST-01**: Add limit increase, structure modifications, settlement, and debt consolidation heuristics
- [x] **INST-02**: Add institution-triggered relief lane
- [x] **INST-03**: Add institution_condition, offer_required_flag, offer_feasibility fields
- [x] **INST-04**: Verify heuristic actions surface in candidate pool behind proper gates

### Multi-Path Recourse Generation
- [x] **PATH-01**: Generate Path A (customer-only), Path B (institution-assisted), and Path C (hybrid) per customer
- [x] **PATH-02**: Ensure independent rankability and internal coherence for each path
- [x] **PATH-03**: Achieve multi_path_rate ≥ target threshold with structurally different paths

### Action Semantics Rendering
- [x] **REND-01**: Add a metric-aware phrasing template system (e.g., "Utilization 27% → 19%")
- [x] **REND-02**: Ensure no broken or generic recommendation text is generated
- [x] **REND-03**: Verify selected plans all produce a coherent narrative summary

### Validation & Cohort Evaluation
- [ ] **EVAL-01**: Implement multi_path_rate, action_diversity_index, non_utilization_action_rate, institution_action_rate, selected_plan_category_distribution metrics
- [ ] **EVAL-02**: Measure structural_cohort_limited reduction effect
- [ ] **EVAL-03**: Ensure no regression in selected_invalid_winner_count, dice_contender_rules, selected-surface consistency, or operator packet coherence

## v2 Requirements

None.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Threshold tuning | Focus is on action semantics, bounds tested in v2.3 |
| Approval uplift optimization (direct) | Indirect focus through diversity |
| Planner redesign | Not in scope for v2.4 |
| Decision policy changes | Preserving v2.2 trust contracts |
| Compliance / live integrations | Future milestone scope |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEM-01 | Phase 54 | Complete |
| SEM-02 | Phase 54 | Complete |
| SEM-03 | Phase 54 | Complete |
| MAP-01 | Phase 55 | Complete |
| MAP-02 | Phase 55 | Complete |
| MAP-03 | Phase 55 | Complete |
| DICE-01 | Phase 56 | Complete |
| DICE-02 | Phase 56 | Complete |
| DICE-03 | Phase 56 | Complete |
| DICE-04 | Phase 56 | Complete |
| INST-01 | Phase 57 | Complete |
| INST-02 | Phase 57 | Complete |
| INST-03 | Phase 57 | Complete |
| INST-04 | Phase 57 | Complete |
| PATH-01 | Phase 58 | Complete |
| PATH-02 | Phase 58 | Complete |
| PATH-03 | Phase 58 | Complete |
| REND-01 | Phase 59 | Complete |
| REND-02 | Phase 59 | Complete |
| REND-03 | Phase 59 | Complete |
| EVAL-01 | Phase 60 | Pending |
| EVAL-02 | Phase 60 | Pending |
| EVAL-03 | Phase 60 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-03*
*Last updated: 2026-04-04 after Phase 59 completion tracking*
