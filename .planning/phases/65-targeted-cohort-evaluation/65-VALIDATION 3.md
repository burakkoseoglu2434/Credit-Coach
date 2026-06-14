---
phase: 65
slug: targeted-cohort-evaluation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-10
---

# Phase 65 - Validation Strategy

> Per-phase validation contract for targeted-vs-global cohort comparison, honesty/control reporting, and deterministic conclusion framing.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-local command in the plan
- **After every plan wave:** Run the quick run command
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 65-01-01 | 01 | 1 | EVAL-01, EVAL-02 | integration | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 65-01-02 | 01 | 1 | EVAL-01, EVAL-02 | integration | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 65-02-01 | 02 | 2 | EVAL-01, EVAL-02 | integration | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 65-02-02 | 02 | 2 | EVAL-02 | regression | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 65-03-01 | 03 | 3 | EVAL-03 | regression | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 65-03-02 | 03 | 3 | EVAL-03 | regression | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_cohort_evaluation.py` already exists and covers the evaluation runner, evidence packaging, artifact writer, and current end-to-end outputs
- [x] the current cohort runner already emits recoverability, recourse-mode, recommendation-mode, and movement-ranking truth needed for Phase 65 comparisons

*If implementation spills outside the cohort-evaluation seam, expand validation before execution.*

---

## Manual-Only Verifications

- All planned Phase 65 behavior should be automatable through the existing cohort-evaluation test surface; no manual-only verification is required if the current evaluation tests are extended as scoped.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths or Wave 0 coverage
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending execution
