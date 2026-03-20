# Requirements: Credit Coach v2.0 Personalized Action & Decision Intelligence

**Status:** Active
**Defined:** 2026-03-20
**Core Value:** Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints, then surface those plans in a form that enterprise buyers and analysts can trust.

## v2.0 Requirements

### Personalized Action Plans

- [ ] **PACT-01**: Each selected plan can be serialized into customer-specific numeric action steps with current value, target value, delta, unit, and due window
- [ ] **PACT-02**: Each action step includes feasibility-safe completion criteria, burden context, and a concrete definition of what “done” means for that customer
- [ ] **PACT-03**: Customer actions and institution actions can coexist in one ordered plan while remaining clearly separated and traceable

### Decision Intelligence

- [ ] **DINT-01**: The system can explain how a personalized plan changes approval readiness, review posture, or offer eligibility for a specific customer across `4w / 12w / 24w`
- [ ] **DINT-02**: Institution-aware dependencies such as approvals, prerequisite actions, and offer conditions are explicit in the plan contract and safe for product use

### Product Narratives

- [ ] **NARR-01**: Engine-owned narratives can explain what the customer should do, why it matters, what numeric effect is expected, and what happens if the step is completed or missed
- [ ] **NARR-02**: Product surfaces can render personalized numeric plans in business-first language by default while keeping numeric and technical detail available on demand

### Portfolio Validation

- [ ] **PVAL-01**: Portfolio evaluation can measure coverage, realism, and outcome distribution for personalized numeric plans instead of only generic recourse outputs
- [ ] **PVAL-02**: Proof artifacts can compare the personalized-action layer against the shipped `v1.3` baseline on customer specificity, decision clarity, and institution awareness

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
| PACT-01 | Phase 26 | Pending |
| PACT-02 | Phase 26 | Pending |
| PACT-03 | Phase 27 | Pending |
| DINT-01 | Phase 27 | Pending |
| DINT-02 | Phase 27 | Pending |
| NARR-01 | Phase 28 | Pending |
| NARR-02 | Phase 28 | Pending |
| PVAL-01 | Phase 29 | Pending |
| PVAL-02 | Phase 29 | Pending |

**Coverage:**
- v2.0 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0

---
*Requirements defined: 2026-03-20*
*Last updated: 2026-03-20 after roadmap creation*
