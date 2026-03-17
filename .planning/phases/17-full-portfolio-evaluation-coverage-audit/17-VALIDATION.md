---
phase: 17
slug: full-portfolio-evaluation-coverage-audit
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-18
---

# Phase 17 - Validation Strategy

> Per-phase validation contract for full-population evaluation, segment-level coverage proof, and portfolio validation review artifacts.

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
| 17-01-01 | 01 | 1 | PORT-01 | summary contract | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_recourse_funnel_kpis.py` | ⬜ planned | ⬜ pending |
| 17-01-02 | 01 | 1 | PORT-01 | full-population tables | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_batch_candidate_diversity.py` | ⬜ planned | ⬜ pending |
| 17-02-01 | 02 | 2 | PORT-01 | segment rollups | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_batch_candidate_diversity.py` | ⬜ planned | ⬜ pending |
| 17-02-02 | 02 | 2 | PORT-01 | seeded mirror integration | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py` | ✅ | ⬜ pending |
| 17-03-01 | 03 | 3 | PORT-01 | executive review generation | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py` | ⬜ planned | ⬜ pending |
| 17-03-02 | 03 | 3 | PORT-01 | curated-vs-proof separation | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py` | ⬜ planned | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` - extend existing batch KPI coverage around whole-population denominators and portfolio-level coverage semantics
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` - protect coverage, offer, and trajectory metrics that Phase 17 will roll up into canonical proof
- [x] `credit-coach/tests/test_phase_experiment_suite.py` - verify seeded suite mirroring and artifact references for the new portfolio proof layer
- [x] `credit-coach/tests/test_portfolio_validation.py` - add dedicated regression coverage for canonical summary JSON, segment breakdowns, and portfolio validation review outputs

---

## Manual-Only Verifications

One human scan is still useful after execution:

- confirm full-population coverage uses the right denominator and does not silently collapse back to denied-only scope
- confirm total-population, denied-population, and recovery-ready denied stories are clearly separated
- confirm segment rollups reuse existing `risk_band`, `income_band`, `stress_band`, and canonical segment keys instead of inventing a new taxonomy
- confirm executive review explicitly labels curated demo stories as illustrative when they are narrower than full portfolio truth
- confirm the new review artifact reads like proof, not like a raw metric dump
- confirm later website phases could consume the new proof artifacts without needing to reinterpret raw internal batch tables

All core behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers canonical summary, segment rollups, suite mirroring, and executive review seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-18
