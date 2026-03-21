# Requirements: Credit Coach v2.0 Personalized Action & Decision Intelligence

**Status:** Active
**Defined:** 2026-03-20
**Core Value:** Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints, then surface those plans in a form that enterprise buyers and analysts can trust.

## v2.0 Requirements

### Action Semantics

- [x] **ACT-01**: Feature-level recourse changes can be mapped deterministically into real-world action types, action groups, and user-facing action contracts

### Numeric Targeting

- [x] **NUM-01**: Selected actions can be translated into customer-specific numeric targets with current value, target value, delta, unit, and due horizon

### Feasibility And Constraints

- [ ] **FEAS-01**: Numeric targets are clipped, repaired, or rejected by explicit feasibility and constraint logic before they are treated as valid plan steps

### Execution Modeling

- [ ] **EXEC-01**: Each action carries a difficulty and execution-likelihood profile that affects plan quality and realistic completion expectations

### Offer Integration

- [ ] **OFFR-01**: Institution actions are represented through an explicit offer layer with terms, approval state, and dependencies that stay separate from customer actions

### Narrative Generation

- [ ] **NARV-01**: Engine-owned narratives can explain personalized numeric and institution-aware plans in product language without losing numeric and technical traceability

### Product Surface

- [ ] **SURF-01**: Demo and product surfaces can render the new numeric personalized plans and decision intelligence directly from typed engine artifacts

### Portfolio Impact

- [ ] **PVAL-01**: Portfolio evaluation can quantify the distribution and impact of personalized numeric plans rather than only generic recourse outputs

### Calibration And Validation

- [ ] **CAL-01**: The system can validate whether suggested numeric targets and resulting impact distributions are realistic, calibrated, and not falsely optimistic

### Pilot Integration

- [ ] **PILT-01**: The personalized planning loop can be exercised against real institution-style data and pilot integration seams without breaking engine-owned truth

## Future Requirements Carried Forward

### Integrations

- **INTG-01**: Institution-specific data exchange can move from curated artifact handoff to pilot-grade inbound and outbound integration contracts
- **INTG-02**: Institution-side policy and offer configuration can be synchronized from external systems instead of milestone-local static contracts

### Explanation And Governance

- **REG-01**: Regulatory explanation and adverse-action communication can expand into richer institution-ready explanation packs
- **REG-02**: Decision intelligence can be packaged for compliance and credit-policy review workflows without reauthoring the core artifact

### Automation

- **AUTO-01**: Proof refresh, release review, and milestone health checks can run as recurring automated workflows
- **AUTO-02**: Personalized-plan validation can be re-run on demand as a scheduled health surface instead of only milestone-time execution

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full borrower self-serve or mobile app experience | This milestone focuses on plan intelligence and enterprise surfaces, not consumer product expansion |
| Autonomous online policy promotion | Evidence-first controls remain the required baseline |
| Institution-specific hardcoded playbooks with no artifact contract | The engine must remain source-of-truth and configurable rather than branch into bespoke undocumented logic |
| Full CRM, LOS, or call-center integration rollout | External integration remains a future requirement after the personalized plan contract is hardened |
| Legal or compliance advice automation | The system remains a decision-support product, not a legal advisor |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ACT-01 | Phase 30 | Satisfied |
| NUM-01 | Phase 31 | Satisfied |
| FEAS-01 | Phase 32 | Pending |
| EXEC-01 | Phase 33 | Pending |
| OFFR-01 | Phase 34 | Pending |
| NARV-01 | Phase 35 | Pending |
| SURF-01 | Phase 36 | Pending |
| PVAL-01 | Phase 37 | Pending |
| CAL-01 | Phase 38 | Pending |
| PILT-01 | Phase 39 | Pending |

**Coverage:**
- v2.0 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0

---
*Requirements defined: 2026-03-20*
*Last updated: 2026-03-20 after roadmap creation*
