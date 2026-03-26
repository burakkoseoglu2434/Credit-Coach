# Requirements: Credit Coach

**Defined:** 2026-03-24
**Core Value:** Generate customer-specific credit action plans that are actionable, behaviorally realistic, governance-safe, and measurably useful enough to improve denied-customer outcomes without breaking enterprise trust.

## v2.2 Requirements

Requirements for `v2.2 Winner Integrity & Consumer Consistency`. Each maps to exactly one roadmap phase.

### Winner Integrity

- [x] **WINT-01**: Collection reruns never select a plan whose `recommendation_validity_status` is `invalid`
- [x] **WINT-02**: If validity filtering empties a preferred candidate subset, planner fallback widens only to other valid candidates or returns no valid winner
- [x] **WINT-03**: Selected customer truth records the winning plan's validity and provenance consistently across raw and flat artifacts

### Dice Lane Enforcement

- [x] **DICE-01**: `dice` candidates carry the same action-level and plan-level validity fields into planner selection as internal candidates
- [x] **DICE-02**: Invalid `dice` candidates remain visible in diagnostics but can never be emitted as selected winners

### Selected Surface Consistency

- [ ] **CONS-01**: `best_plan_id`, selected plan rows, external decision summaries, and collection metrics remain mutually consistent for each customer
- [ ] **CONS-02**: No external `CONDITIONAL` output points at a selected plan row whose plan status is `REJECTED`
- [ ] **CONS-03**: Operator packets and explanation packs render recommendation text from the selected valid plan only, with no leakage from discarded invalid winners

### Operator Packet Coherence

- [ ] **OPER-01**: Operator short view never renders an invalid selected recommendation as a recommended next action
- [ ] **OPER-02**: Approved packets with no active drivers render no fallback blockers
- [ ] **OPER-03**: Warning badges and appendix diagnostics remain available without creating contradictory short-view guidance

## v2 Requirements

Deferred until winner integrity and consumer consistency are proven.

### Threshold and Outcome Optimization

- **THR-01**: Decision thresholds can be widened safely using validity-clean winner evidence
- **APRV-01**: Approval and conditional rates can be optimized without degrading selected-surface trust

### Offer and Readiness Expansion

- **OFFR-01**: Offer-maturity lanes can improve business outcomes instead of remaining descriptive only
- **READ-01**: Readiness semantics can be widened into a larger movable queue once selected truth is stable

## Out of Scope

Explicitly excluded from `v2.2` to keep the milestone focused.

| Feature | Reason |
|---------|--------|
| Decision-threshold widening | Winner integrity must be fixed before approval aggressiveness is tuned |
| Approval-rate optimization | Uplift tuning would hide the current selected-winner trust problem |
| Redesign of Phases 40 / 40.5 / 41 / 42 / 42.5 / 43 | These remain fixed baselines for this milestone |
| New borrower-facing self-serve surfaces | Consumer-surface consistency here means operator and explanation outputs, not new channels |
| Live institution integrations or compliance automation | Not required to fix selected-winner integrity |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| WINT-01 | Phase 45 | Complete |
| WINT-02 | Phase 45 | Complete |
| WINT-03 | Phase 45 | Complete |
| DICE-01 | Phase 46 | Complete |
| DICE-02 | Phase 46 | Complete |
| CONS-01 | Phase 47 | Pending |
| CONS-02 | Phase 47 | Pending |
| CONS-03 | Phase 47 | Pending |
| OPER-01 | Phase 48 | Pending |
| OPER-02 | Phase 48 | Pending |
| OPER-03 | Phase 48 | Pending |

**Coverage:**
- v2.2 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0 ✓

## Validated

- ✓ Core PD modeling, calibration, and deterministic backend controls exist in the codebase - v1.0
- ✓ Gate-aligned recourse generation, feasibility controls, and high-risk or trajectory flows exist in the codebase - v1.0
- ✓ Fairness, stress, benchmark, challenger, telemetry, and release-gate workflows exist in the codebase - v1.0
- ✓ Seeded fairness, KPI contract, candidate-quality, telemetry evidence, and outcome-feedback packaging are hardened - v1.1
- ✓ Recommendation quality is now typed-action-aware, behavior-aware, trajectory-aware, offer-aware, and learning-loop-capable - v1.2
- ✓ Portfolio proof, business-first product surfaces, analyst validation, and pilot-baseline demo ops are now shipped and audited - v1.3
- ✓ Personalized action intelligence is now semantic, numeric, feasible, execution-aware, institution-aware, portfolio-validated, and pilot-package-ready - v2.0
- ✓ Deterministic decision ownership, contract trust repair, cohort calibration, operator review packs, planner source-mix honesty, and repeatable pilot refresh now ship together as one audited baseline - v2.1
- ✓ Post-v2.1 Phase `42.5 Recommendation Validity Layer` now hardens numeric recommendations with canonical validity evaluation, hard-invalid contender filtering, warning penalties, operator sanity badges, explanation-pack human-review propagation, and additive collection metrics
- ✓ Phase `46 Dice Lane Validity Enforcement` now converges DICE onto the shared typed-action contract, adds lane-specific completeness and semantic-quality truth, keeps diagnostics visible while gating planner contention on DICE eligibility, and proves selected DICE cleanliness with `selected_dice_valid_rate = 1.0` across three 250-customer reruns

---
*Requirements defined: 2026-03-24*
*Last updated: 2026-03-26 after completing Phase 46*
