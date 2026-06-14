---
phase: 37
slug: portfolio-level-numeric-impact
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-22
---

# Phase 37 - Validation Strategy

> Per-phase validation contract for portfolio-level numeric burden, execution-aware payoff, segment insight, and business-safe portfolio review packaging.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py tests/test_kpi_contract.py tests/test_batch_candidate_diversity.py -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_portfolio_validation.py -q`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 37-01-01 | 01 | 1 | PVAL-01 | canonical numeric-impact summary and burden/payoff contract | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py -q` | ✅ | ⬜ pending |
| 37-01-02 | 01 | 1 | PVAL-01 | batch artifact emission and portfolio numeric-impact table integrity | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py -q` | ✅ | ⬜ pending |
| 37-02-01 | 02 | 2 | PVAL-01 | segment priority and execution-aware aggregation | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py -q` | ✅ | ⬜ pending |
| 37-02-02 | 02 | 2 | PVAL-01 | offer-supported realized payoff and segment insight outputs | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_kpi_contract.py -q` | ✅ | ⬜ pending |
| 37-03-01 | 03 | 3 | PVAL-01 | business-vs-technical portfolio review packaging | `cd credit-coach && python -m pytest tests/test_kpi_contract.py tests/test_portfolio_validation.py -q` | ✅ | ⬜ pending |
| 37-03-02 | 03 | 3 | PVAL-01 | suite/proof alignment and regression closure | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py tests/test_kpi_contract.py tests/test_batch_candidate_diversity.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_portfolio_validation.py` — existing portfolio-proof seam can validate numeric-impact summary and breakdown behavior
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — suite packaging tests can validate scale/seed aggregation and artifact mirroring
- [x] `credit-coach/tests/test_kpi_contract.py` — business review output tests can validate headline/supporting metric packaging
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` — batch summary regression seam can absorb additional portfolio artifact outputs without breaking pipeline assumptions

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm the business headline reads as:
  - numeric plan coverage
  - requested change burden
  - execution-aware realization
  - execution-aware portfolio payoff
- confirm `realization_gap` appears as a first-class supporting metric rather than disappearing into technical detail
- confirm business segment output stays concise and names:
  - highest payoff segment
  - highest burden / lowest realization segment
  - offer-dependent segment
- confirm mixed-unit requested change is not reported as a naive raw-delta average
- confirm technical artifacts still expose full unit-family and segment breakdown transparency

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity preserved across all execution waves
- [x] Wave 0 covers portfolio summary, suite packaging, KPI review, and batch artifact stability
- [x] No watch-mode flags
- [x] Feedback latency acceptable for iterative execution
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-22
