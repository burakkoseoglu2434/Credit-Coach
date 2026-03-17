---
phase: 17
slug: full-portfolio-evaluation-coverage-audit
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-18
---

# Phase 17 - Validation Strategy

> Per-phase validation contract for full-population portfolio proof, reality-gap diagnostics, demo representativeness, and product-ready coverage reporting.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_recourse_funnel_kpis.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_recourse_funnel_kpis.py tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py` |
| **Estimated runtime** | ~50 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_recourse_funnel_kpis.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | PORT-01 | full-dataset summary | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_recourse_funnel_kpis.py` | ⬜ planned | ⬜ pending |
| 17-01-02 | 01 | 1 | PORT-01 | coverage taxonomy and reality-gap base tables | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_batch_candidate_diversity.py` | ⬜ planned | ⬜ pending |
| 17-02-01 | 02 | 2 | PORT-01 | segment and slice rollups | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_batch_candidate_diversity.py` | ⬜ planned | ⬜ pending |
| 17-02-02 | 02 | 2 | PORT-01 | behavior-aware, offer, and trajectory diagnostics | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py` | ✅ | ⬜ pending |
| 17-03-01 | 03 | 3 | PORT-01 | executive review generation | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_recourse_funnel_kpis.py` | ⬜ planned | ⬜ pending |
| 17-03-02 | 03 | 3 | PORT-01 | demo representativeness and curated-vs-cohort separation | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py` | ⬜ planned | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` - extend whole-population KPI semantics beyond denied-only uplift so coverage taxonomy and denominator logic remain stable
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` - protect candidate coverage, feasibility, product-ready, and breakdown semantics needed for portfolio proof
- [x] `credit-coach/tests/test_phase_experiment_suite.py` - verify seeded suite mirroring and supporting references for full-cohort proof and demo-representativeness outputs
- [x] `credit-coach/tests/test_portfolio_validation.py` - add dedicated coverage for canonical portfolio summary, reality-gap flags, offer diagnostics, trajectory classes, and executive review outputs

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm the engine is run across the **full available evaluation population**, not just a denied-only subset reused as the default denominator
- confirm `raw`, `valid`, `governance_safe`, and `product_ready` coverage are all explicit and not collapsed into one headline number
- confirm reality-gap diagnostics are present and can highlight suspiciously idealized or engine-native outputs
- confirm segment reporting is strategic rather than decorative, including meaningful slices such as recoverability, offer-needed, and short-term-vs-long-horizon profile differences
- confirm behavior-aware metrics are compared against nominal quality so the phase can explain what realism costs or improves
- confirm offer diagnostics are separately visible rather than diluted into global plan coverage
- confirm trajectory classes can distinguish early-healthy from delayed-only or long-horizon-heavy plans
- confirm demo representativeness is explicitly labeled, including whether the website story is representative, optimistic, or narrow
- confirm executive review output reads like stakeholder-facing proof rather than raw metric dump

All core behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers full-population summary, coverage taxonomy, segment proof, behavior-aware diagnostics, offer diagnostics, and demo representativeness
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-18
