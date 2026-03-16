# Requirements: Credit Coach v1.2 Recommendation Quality Hardening

**Defined:** 2026-03-15
**Core Value:** Generate credit recourse plans that are actionable, behaviorally realistic, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints.

## v1.2 Requirements

### Action Realism & Feasibility Expansion

- [x] **REC-01**: System can represent behavioral, structural, and institutional recommendation actions through one explicit action taxonomy
- [x] **REC-02**: Feasibility rules can block unrealistic financial transitions using monthly-change, income-growth, utilization, and capacity constraints
- [x] **REC-03**: Planner can detect action dependencies or conflicts so invalid combinations are rejected before ranking

### Behavior-Aware Recourse

- [x] **REC-04**: Each candidate action or plan can carry an estimated execution probability grounded in customer or plan context
- [x] **REC-05**: Planner scoring can use expected utility and partial-execution behavior without weakening fairness, reliability, or telemetry inheritance

### Sequential Recourse Planning

- [x] **REC-06**: Planner can generate phased recommendation trajectories for 0-4 weeks, 1-3 months, and 3-12 months rather than only one-shot plans
- [x] **REC-07**: Trajectory simulation can model timing, partial execution, and dynamic risk evolution so short-term improvements do not hide long-term harm

### Policy Optimization Layer

- [x] **REC-08**: Institution-side offer actions can appear in candidate plans and be ranked beside user-driven recourse actions
- [x] **REC-09**: Offer optimization can improve recovery proxies without increasing risk, fairness, or reliability violations

### Outcome Feedback & Learning Loop

- [x] **REC-10**: Decision logging can persist recommendation, offer, and context details needed for downstream learning
- [x] **REC-11**: Outcome ingestion and off-policy evaluation can learn from action completion, payment behavior, default events, and recovery results

## Future Requirements

### Productization

- **PROD-01**: Operator-facing dashboards summarize milestone health without reading raw artifacts
- **PROD-02**: Regulatory explanation layer expands from technical XAI outputs to user-facing adverse-action narratives
- **PROD-03**: Release review and milestone health checks run on a recurring automated schedule

## Out of Scope

| Feature | Reason |
|---------|--------|
| New borrower-facing or mobile-first product surfaces | This milestone remains focused on the recommendation engine rather than end-user UX |
| Full online autonomous learning or policy promotion | Outcome learning is milestone scope; production auto-promotion remains later-stage work |
| Legal or compliance opinion automation | The system continues to define engineering and governance patterns, not legal advice |
| Mandatory external institution integrations for every workflow | Offer and outcome logic can start from internal artifacts before external system wiring becomes mandatory |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REC-01 | Phase 12 | Complete |
| REC-02 | Phase 12 | Complete |
| REC-03 | Phase 12 | Complete |
| REC-04 | Phase 13 | Complete |
| REC-05 | Phase 13 | Complete |
| REC-06 | Phase 14 | Complete |
| REC-07 | Phase 14 | Complete |
| REC-08 | Phase 15 | Complete |
| REC-09 | Phase 15 | Complete |
| REC-10 | Phase 16 | Complete |
| REC-11 | Phase 16 | Complete |

**Coverage:**
- v1.2 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0

---
*Requirements defined: 2026-03-15*
*Last updated: 2026-03-16 after completing Phase 16*
