# Requirements: Credit Coach v2.1 Decision Ownership & Pilot-Ready Trust

**Defined:** 2026-03-23
**Core Value:** Transform the system from a decision-intelligence prototype into a deterministic, pilot-ready fintech decision system.

## v2.1 Requirements

### Contract And Trust

- [ ] **TRST-01**: Single-customer and collection artifacts emit null-free decision-critical fields and checkpoint statuses across raw and flat outputs
- [ ] **TRST-02**: Raw and flat customer decision artifacts stay parity-checked and classify contract faults without exposing `NEEDS_REVIEW` on business-facing surfaces

### Decision Ownership

- [ ] **DEC-01**: Every customer receives deterministic internal and business-visible decision states using ordered policy logic, confidence gating, readiness gating, and zero-step rejection
- [ ] **DEC-02**: Every non-rejected customer receives a one-line business explanation, structured numeric drivers, decision confidence, expected readiness, and upgrade condition
- [ ] **DEC-03**: Offer maturity, conditional subtype, and rejection subtype truth explicitly determine whether a customer can be approved, conditional, or rejected

### Cohort And Calibration

- [ ] **CAL-01**: Collection runs can evaluate decision funnels across mixed and stress-test cohorts with approve, conditional, rejected, and internal review shares
- [ ] **CAL-02**: Decision thresholds can be tuned against cohort-level readiness, confidence-aware quality signals, false-positive proxy, and policy-version comparisons

### Operator Workflow

- [ ] **OPS-01**: Operators can review 50 customers from one collection run in under 30 minutes using short decision packs with blockers, readiness, downside risk, and offer state
- [ ] **OPS-02**: Collection summary and manifest expose pilot-review signals such as decision funnel, contract health, dominant rejection reasons, and conditional hot spots

### Planner Quality

- [ ] **PLAN-01**: Best-plan selection eliminates zero-action winners, reports source mix, and improves internal planner competitiveness versus `dice`, `rule`, and `fallback` candidates

### Production Pilot Baseline

- [ ] **PROD-01**: Deterministic decision-policy runs can be versioned, compared, and rerun through artifact QA and pilot refresh workflows
- [ ] **PROD-02**: Institution-facing pilot docs and explanation packs can package deterministic decision policy without leaking internal-only states

## Future Requirements

### External Integrations

- **INTG-01**: Institution-specific inbound and outbound integrations can move from pilot packages to live system contracts
- **INTG-02**: Institution policy and offer configuration can synchronize continuously from external systems

### Governance And Automation

- **REG-01**: Adverse-action and regulatory explanation packs can expand into institution-ready compliance workflows
- **AUTO-01**: Proof refresh, release review, and milestone health checks can run as recurring automated workflows

## Out of Scope

| Feature | Reason |
|---------|--------|
| Borrower self-serve or mobile product expansion | `v2.1` focuses on deterministic institution-facing decisions, not consumer channel expansion |
| Live online policy promotion | Decision ownership must be hardened before autonomous policy rollout is considered |
| Full LOS, CRM, or call-center integration rollout | This milestone stops at pilot-ready package and decision review baselines |
| Legal or compliance opinion automation | The system remains decision-support and explanation tooling, not legal advice software |
| Rebuilding the core recourse or website stacks from scratch | The milestone must evolve the shipped brownfield contracts rather than replace them |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TRST-01 | Phase 40 | Pending |
| TRST-02 | Phase 40 | Pending |
| DEC-01 | Phase 40.5 | Pending |
| DEC-02 | Phase 40.5 | Pending |
| DEC-03 | Phase 40.5 | Pending |
| CAL-01 | Phase 41 | Pending |
| CAL-02 | Phase 41 | Pending |
| OPS-01 | Phase 43 | Pending |
| OPS-02 | Phase 43 | Pending |
| PLAN-01 | Phase 42 | Pending |
| PROD-01 | Phase 44 | Pending |
| PROD-02 | Phase 44 | Pending |

**Coverage:**
- v2.1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-23 after milestone v2.1 initialization*
