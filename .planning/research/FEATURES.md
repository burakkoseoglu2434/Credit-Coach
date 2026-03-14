# Feature Research

**Domain:** Brownfield credit recourse system fairness-stability and KPI-hardening milestone
**Researched:** 2026-03-14
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Multi-seed fairness stability reporting | Release decisions cannot rely on a lucky single run | MEDIUM | Needs shared seed summaries and aggregate acceptance checks |
| Unified KPI contract across smoke, suite, and challenger flows | Operators need one source of truth for GO/NO_GO | MEDIUM | Historical reports show contract drift was a real blocker |
| Intersecting segment and candidate-source diagnostics | Aggregate fairness numbers are not enough to debug regressions | HIGH | Must explain which segment and which generator path caused failures |
| Deterministic experiment freeze (`train_once`) | Comparisons are not trustworthy without model-state control | LOW | Already partially implemented; milestone should standardize usage |
| Telemetry-required production profile | Production evidence is incomplete if telemetry can silently be skipped | MEDIUM | Needs fail-closed behavior in release evaluation |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Short-term / phase-1 fast-track objective | Makes recourse guidance feel actionable earlier for denied customers | MEDIUM | Already prototyped in recent reports and worth hardening |
| Candidate diversity and source-entropy measurement | Helps prove the planner is exploring meaningful alternatives | HIGH | Valuable for research credibility and benchmark interpretation |
| Outcome-feedback delta reporting | Connects offline KPI movement to repayment/business proxies | HIGH | Strong differentiator for thesis-to-product maturity |
| Regulatory-grade reason diagnostics | Makes release reviews and adverse-action narratives more robust | HIGH | Valuable, but likely phase-late or next-milestone work |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Chasing the best single-run lift only | It looks like quick progress | It hides fairness and stability regressions | Use repeated seeded acceptance criteria |
| One giant “fairness score” | It simplifies dashboards | It obscures which segment, source, or horizon failed | Keep decomposed metrics and root-cause tables |
| Always-on broad search expansion | It can raise lift locally | It often blows up latency and runtime variance | Use gated search budgets and targeted source expansion |

## Feature Dependencies

```text
Unified KPI contract
    └──requires──> deterministic experiment freeze
                           └──supports──> multi-seed fairness stability

Intersecting fairness diagnostics
    └──requires──> candidate source attribution

Outcome-feedback reporting
    └──requires──> reproducible release evidence
                           └──requires──> telemetry-required prod profile
```

### Dependency Notes

- **Unified KPI contract requires deterministic experiment freeze:** contract checks are meaningless if each run uses a different model state.
- **Intersecting fairness diagnostics require candidate source attribution:** fairness failures need to be tied to internal vs DiCE or other generator paths.
- **Outcome-feedback reporting requires reproducible release evidence:** downstream outcome analysis is only trustworthy when experiment inputs and outputs are frozen.

## MVP Definition

### Launch With (v1.1)

- [x] Multi-seed fairness stability suite — proves release decisions are not single-run accidents
- [x] Unified KPI contract across smoke, suite, and challenger flows — prevents gate drift
- [x] Segment x source fairness diagnostics — makes failures actionable
- [x] Telemetry-required production profile — guarantees evidence completeness

### Add After Validation (v1.1.x)

- [ ] Candidate diversity / source entropy reporting — add once core stability contract is trusted
- [ ] Short-term phase-1 fast-track tuning — add after fairness diagnostics show safe room to optimize
- [ ] Outcome-feedback delta reporting — add once release evidence is standardized

### Future Consideration (v2+)

- [ ] Regulatory explanation workbench — defer until core KPI stability is reliable
- [ ] Operator-facing milestone dashboard — defer until the evidence model stops changing

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Multi-seed fairness stability suite | HIGH | MEDIUM | P1 |
| Unified KPI contract | HIGH | MEDIUM | P1 |
| Segment x source diagnostics | HIGH | HIGH | P1 |
| Telemetry-required production profile | HIGH | MEDIUM | P1 |
| Candidate diversity reporting | MEDIUM | HIGH | P2 |
| Short-term fast-track tuning | MEDIUM | MEDIUM | P2 |
| Outcome-feedback reporting | HIGH | HIGH | P2 |

## Competitor Feature Analysis

| Feature | Research Baselines | Existing Brownfield State | Our Approach |
|---------|--------------------|---------------------------|--------------|
| Fairness diagnostics | Fairlearn-style post-processing and `MetricFrame` analysis | Basic fairness and stress artifacts already exist | Add seeded, intersecting, source-aware stability reporting |
| Candidate quality | DiCE / FACE / CARLA style diversity and feasible-path thinking | Mixed internal + DiCE generation already exists | Measure diversity explicitly and relate it to KPI outcomes |
| Release gating | Published KPI and governance contracts | Smoke, suite, and challenger flows exist but drift | Unify the contract and fail semantics across all three |

## Sources

- `.planning/research/legacy/THREE_PILLAR_RESEARCH_TO_IMPLEMENT_PLAN_20260309.md`
- `.planning/research/legacy/P0_P1_BACKLOG_RESEARCH_20260308.md`
- `.planning/archive/legacy-reports/CONTINUE_P0_FASTTRACK_EXECUTION_REPORT_20260310.md`
- `.planning/archive/legacy-reports/PHASE_TRAJECTORY_GATEFIX_EXECUTION_REPORT_20260310.md`

---
*Feature research for: fairness-stability and KPI-hardening milestone*
*Researched: 2026-03-14*
