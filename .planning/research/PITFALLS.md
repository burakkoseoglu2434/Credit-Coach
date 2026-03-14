# Pitfalls Research

**Domain:** Brownfield credit recourse system fairness-stability and KPI-hardening milestone
**Researched:** 2026-03-14
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Optimizing lift while fairness stability collapses

**What goes wrong:**
Single-run lift improves, but repeated seeded runs fail equalized-odds, fairness-gap, or recourse-success checks.

**Why it happens:**
The system has enough tuning power to move business KPIs quickly, while fairness regressions show up only under repeated or intersecting analysis.

**How to avoid:**
Make seeded fairness stability part of milestone acceptance, not just aggregate batch reporting.

**Warning signs:**
- One run passes and the next fails with similar configs
- Aggregate lift stays strong while fairness delta swings by seed or segment

**Phase to address:**
Phase 8

---

### Pitfall 2: Contract drift across smoke, suite, and challenger flows

**What goes wrong:**
Different commands report different pass/fail conclusions for the same underlying behavior.

**Why it happens:**
Threshold logic and metric naming evolve separately inside large CLI modules.

**How to avoid:**
Refactor to a shared KPI contract and require every gate-producing command to use it.

**Warning signs:**
- Same metric has different names or thresholds across outputs
- A fix “works” in one runner but not the others

**Phase to address:**
Phase 9

---

### Pitfall 3: Candidate diversity remains invisible behind aggregate gate-pass rate

**What goes wrong:**
The system appears stable, but all gains come from one narrow generator path and collapse when distribution shifts.

**Why it happens:**
Batch summaries focus on final gate outcomes, not on how broadly the planner explored alternatives.

**How to avoid:**
Track source entropy, generator mix, and segment-by-source outcomes beside aggregate KPIs.

**Warning signs:**
- Nearly all winning plans come from one source
- DiCE or internal generators appear “unused” without clear explanation

**Phase to address:**
Phase 10

---

### Pitfall 4: Telemetry remains optional in production-like decisions

**What goes wrong:**
Runs can be declared healthy without the monitoring evidence needed to trust them in production.

**Why it happens:**
Telemetry was added as a capability before it was enforced as a release requirement.

**How to avoid:**
Make production profile telemetry fail closed and include exporter success in release evidence.

**Warning signs:**
- Smoke can pass while telemetry is disabled
- Export success metrics are missing or ignored

**Phase to address:**
Phase 11

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Cloning experiment YAML files for every tuning pass | Fast iteration | Comparison and rollback become error-prone | Acceptable only during short-lived exploration, not for canonical milestone configs |
| Keeping contract logic inside giant CLI files | Fewer files today | High regression risk and duplicated semantics | Acceptable only temporarily while extracting shared helpers |
| Judging milestone health from one attractive run | Fast optimism | False confidence and poor release discipline | Never for milestone acceptance |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Telemetry endpoint | Treating export as best-effort only | Record exporter success and gate production readiness on it |
| Fairness toolkit / post-processing | Applying fairness changes without recourse-actionability review | Evaluate fairness changes alongside lift, feasibility, and source diagnostics |
| Benchmark harness | Comparing benchmark output to production flow without aligned metrics | Normalize metrics and artifact schemas first |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Broad candidate search expansion | p95/p99 explode during 1000-customer runs | Use search-budget guards and per-segment targeting | Breaks under production-like batch scale |
| Extra diagnostics added directly to hot path | Debug value increases while runtime becomes noisy | Write richer artifacts, but keep expensive analysis optional or post-run | Breaks when every seed run computes all tables inline |
| Re-training in every suite path | Runtime and variance increase together | Freeze training once and reuse model state | Breaks as soon as milestone acceptance depends on repeated seeds |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Leaving insecure API mode available beyond local/demo use | Unauthorized scoring or control-plane misuse | Restrict or hard-fail insecure mode outside development |
| Emitting telemetry to arbitrary endpoints without auth expectations | Evidence leakage or silent ingestion failure | Validate endpoints and add authenticated export where needed |
| Expanding diagnostic artifacts without review | Sensitive operational data leaks into report bundles | Keep artifact scope deliberate and document what belongs in release evidence |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Reporting only that a run failed | Operators cannot tell what to fix next | Always include root-cause breakdown and failed gate details |
| Over-promising short-term success from a tuned plan | Denied customers get unrealistic guidance | Tie fast-track claims to explicit feasibility and trajectory evidence |
| Mixing benchmark and production language | Decision-makers misread research artifacts as production truth | Separate “research evidence” from “release decision evidence” clearly |

## "Looks Done But Isn't" Checklist

- [ ] **Fairness stability:** Often missing seed-level variance — verify 5-seed aggregate and per-seed failure tables
- [ ] **KPI contract:** Often missing cross-runner alignment — verify smoke, suite, and challenger semantics match
- [ ] **Telemetry enforcement:** Often missing fail-closed behavior — verify prod profile fails if telemetry is absent
- [ ] **Short-term trajectory:** Often missing realistic 4-week acceptance bounds — verify 4w, 12w, and 24w gates are all intentional

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Fairness instability | HIGH | Freeze model state, inspect segment/source diagnostics, retune policy with repeated seeds |
| Contract drift | MEDIUM | Centralize threshold definitions, regenerate gate rows, re-baseline tests |
| Candidate diversity blind spot | MEDIUM | Add provenance metrics, compare source mix by segment, retune search quotas |
| Missing telemetry enforcement | LOW | Enable fail-closed checks, add exporter success assertions, regenerate smoke evidence |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Fairness stability collapse | Phase 8 | 5-seed fairness summary remains inside contract bounds |
| Contract drift | Phase 9 | Smoke, suite, and challenger outputs agree on the same evidence |
| Candidate diversity invisibility | Phase 10 | Source entropy and generator contribution tables are present |
| Telemetry optionality | Phase 11 | Production profile fails when telemetry evidence is missing |

## Sources

- `.planning/research/legacy/THREE_PILLAR_RESEARCH_TO_IMPLEMENT_PLAN_20260309.md`
- `.planning/research/legacy/P0_SPRINT_FIX_PLAN_20260308.md`
- `.planning/archive/legacy-reports/RETRY_EXECUTION_REPORT_20260309.md`
- `.planning/archive/legacy-reports/PHASE_TRAJECTORY_GATEFIX_EXECUTION_REPORT_20260310.md`

---
*Pitfalls research for: fairness-stability and KPI-hardening milestone*
*Researched: 2026-03-14*
