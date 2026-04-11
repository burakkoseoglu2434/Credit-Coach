---
phase: 68
slug: real-cohort-evidence-run
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-11
---

# Phase 68 — Validation Strategy

> Validation contract for running an evidence-grade cohort evaluation and packaging outcomes into audit-safe reports without changing runtime behavior.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + lightweight CLI/output checks |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_outcome_feedback.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_outcome_feedback.py -q` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run Quick run command
- **After every plan wave:** Run Full suite command
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 68-01-01 | 01 | 1 | EVID-01 | regression | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 68-02-01 | 02 | 2 | EVID-02 | regression | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py -q` | ✅ | ⬜ pending |
| 68-03-01 | 03 | 3 | EVID-03 | manual + scripted | `rg -n \"causal\\b|uplift\\b|guarantee\\b|proves\\b|increases approvals\" .planning/phases/68-real-cohort-evidence-run/68-COHORT-REPORT.md .planning/phases/68-real-cohort-evidence-run/68-EXECUTIVE-SUMMARY.md || true` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all Phase 68 needs:
- `credit-coach/tests/test_cohort_evaluation.py` — cohort runner contract + metrics emission
- `credit-coach/tests/test_outcome_feedback.py` — realized-outcome seam + non-causal reporting

---

## Manual-Only Verifications

One short manual scan is recommended after Wave 3:
- confirm the investor summary makes **no causal claims**
- confirm “capability concentration” and “realized outcomes” are separated explicitly
- confirm sampling mode (with/without replacement) is stated clearly

---

## Validation Sign-Off

- [x] All tasks have automated verify or bounded manual checks
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all dependencies
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
