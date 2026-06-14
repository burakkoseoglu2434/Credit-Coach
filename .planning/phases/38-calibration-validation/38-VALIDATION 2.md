---
phase: 38
slug: calibration-validation
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-22
---

# Phase 38 - Validation Strategy

> Per-phase validation contract for personalized numeric-plan realism, false-optimism control, range stability, drift detection, and business-safe validation review packaging.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py tests/test_kpi_contract.py tests/test_batch_candidate_diversity.py -q` |
| **Estimated runtime** | ~50 seconds |

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
| 38-01-01 | 01 | 1 | CAL-01 | canonical calibration summary and realism or optimism contract | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py -q` | ✅ | ⬜ pending |
| 38-01-02 | 01 | 1 | CAL-01 | row-level validation ingredients and batch artifact integrity | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py -q` | ✅ | ⬜ pending |
| 38-02-01 | 02 | 2 | CAL-01 | segment and unit-family calibration breakdowns | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py -q` | ✅ | ⬜ pending |
| 38-02-02 | 02 | 2 | CAL-01 | drift, narrowness, and instability rollups | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_batch_candidate_diversity.py -q` | ✅ | ⬜ pending |
| 38-03-01 | 03 | 3 | CAL-01 | business-vs-technical validation review packaging | `cd credit-coach && python -m pytest tests/test_kpi_contract.py tests/test_portfolio_validation.py -q` | ✅ | ⬜ pending |
| 38-03-02 | 03 | 3 | CAL-01 | suite or proof alignment and regression closure | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py tests/test_kpi_contract.py tests/test_batch_candidate_diversity.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_portfolio_validation.py` - existing portfolio summary seam can validate realism, optimism, stability, and drift rollups
- [x] `credit-coach/tests/test_phase_experiment_suite.py` - suite packaging tests can validate seed-level and run-level validation aggregation
- [x] `credit-coach/tests/test_kpi_contract.py` - business review output tests can validate validation verdict and supporting metric packaging
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` - batch or distribution regression seam can absorb new drift and narrowness outputs without pipeline breakage

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm validation outputs explicitly surface false optimism instead of hiding it behind strong nominal payoff
- confirm unstable target ranges or narrow distributions are visible in the review output
- confirm "more honest but narrower" can appear as a valid outcome instead of being mislabeled as success or failure
- confirm business review stays concise while technical artifacts preserve full segment, unit-family, and drift transparency
- confirm Phase 38 does not reopen target-generation or feasibility contracts

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity preserved across all execution waves
- [x] Wave 0 covers portfolio validation, suite packaging, KPI review, and batch-distribution stability
- [x] No watch-mode flags
- [x] Feedback latency acceptable for iterative execution
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-22
