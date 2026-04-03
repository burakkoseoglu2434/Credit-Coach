# Requirements: Credit Coach v2.3 Threshold & Outcome Optimization

**Defined:** 2026-04-02
**Core Value:** Generate customer-specific credit action plans that are actionable, behaviorally realistic, governance-safe, and measurably useful enough to improve denied-customer outcomes without breaking enterprise trust.

## v1 Requirements

### Threshold Calibration

- [x] **THR-01**: Pilot reviewers can evaluate bounded threshold-policy profiles on existing winner-clean artifacts without reopening invalid-winner or selected-surface drift behaviors
- [x] **THR-02**: Analysts can compare candidate threshold policies on approval share, conditional share, reject share, readiness mix, and bounded false-positive proxy across the standard cohorts
- [x] **THR-03**: Raw, flat, and collection artifacts can record which threshold-policy profile produced each evaluated run and each promoted recommendation

### Offer and Readiness Outcomes

- [x] **OUT-01**: Existing offer-maturity signals can upgrade eligible customers from `REJECTED` to `CONDITIONAL` or `APPROVED` under explicit bounded rules
- [x] **OUT-02**: Existing readiness signals can upgrade eligible customers from `REJECTED` to `CONDITIONAL` or from `CONDITIONAL` to `APPROVED` under explicit bounded rules
- [x] **OUT-03**: Operator and explanation surfaces can state when offer or readiness rules changed the decision outcome without drifting from the selected consumer truth

### Funnel Movement Guardrails

- [x] **FUN-01**: Portfolio reviewers can measure `REJECTED -> CONDITIONAL -> APPROVED` movement for each candidate policy across `pilot_mixed`, `risk_band_balanced`, and `offer_needed_balanced`
- [x] **FUN-02**: Candidate policies are blocked from promotion if they break shipped trust invariants or worsen bounded risk proxies beyond explicit limits
- [x] **FUN-03**: Portfolio outputs can separate yield gained from threshold movement versus yield gained from offer/readiness outcome rules

### Preferred Policy Promotion

- [ ] **POL-01**: Pilot teams can refresh the standard artifact bundle under one preferred policy profile and compare it directly against the shipped `v2.2` baseline
- [ ] **POL-02**: Pilot teams can carry one preferred policy profile and one fallback profile into demos and first customer conversations with explicit cohort evidence and guardrail status

## v2 Requirements

### Recourse Capability Expansion

- **ACT-01**: The recommendation engine can expand beyond the current action space and generate materially more diverse numeric solution paths
- **ACT-02**: New action families can be introduced without weakening the shipped winner-integrity and consumer-consistency contracts

### Edge-Case Operating Envelope

- **EDGE-01**: Large-sample reruns can validate naturally occurring `no_valid_winner` cases under broadened operating conditions
- **EDGE-02**: Collection reruns can eliminate the remaining pandas concat warnings in batch artifact assembly

## Out of Scope

| Feature | Reason |
|---------|--------|
| Expanding action semantics or opening new recommendation feature space | This milestone is limited to threshold and outcome optimization on top of the shipped action baseline |
| Redesigning Phases `40`, `40.5`, `41`, `42`, `42.5`, `43`, `45`, `46`, `47`, or `48` | These trust and ownership layers are fixed baselines for v2.3 |
| Approval-rate optimization without bounded guardrails | Yield work must stay tied to trust invariants and explicit risk proxies |
| New borrower-facing channels, live institution integrations, or compliance automation | Not required to prove threshold and outcome optimization for pilot conversations |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| THR-01 | Phase 49 | Complete |
| THR-02 | Phase 49 | Complete |
| THR-03 | Phase 49 | Complete |
| OUT-01 | Phase 50 | Complete |
| OUT-02 | Phase 50 | Complete |
| OUT-03 | Phase 50 | Complete |
| FUN-01 | Phase 51 | Complete |
| FUN-02 | Phase 51 | Complete |
| FUN-03 | Phase 51 | Complete |
| POL-01 | Phase 53 | Pending |
| POL-02 | Phase 53 | Pending |

**Coverage:**
- v1 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-03 after Phase 51 completion*
