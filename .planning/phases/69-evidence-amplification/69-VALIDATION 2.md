---
phase: 69
slug: 69-evidence-amplification
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-11
---

# Phase 69 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_cohort_evaluation.py -q` |
| **Full suite command** | `cd credit-coach && PYTHONPATH=src python -m pytest -q` |
| **Estimated runtime** | ~60–180 seconds (quick) / repo-dependent (full) |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_cohort_evaluation.py -q`
- **After every plan wave:** Run `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_cohort_evaluation.py tests/test_outcome_feedback.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~180 seconds (quick slice)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 69-01-01 | 01 | 1 | n/a | unit/integration | `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 69-02-01 | 02 | 2 | n/a | unit/integration | `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_outcome_feedback.py -q` | ✅ | ⬜ pending |
| 69-03-01 | 03 | 3 | n/a | integration | `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers Phase 69 (pytest present; cohort eval + outcome feedback test modules exist).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Evidence docs contain no banned causal/uplift language | n/a | Report text is generated from artifacts | Grep the Phase 69 generated `*.md` files for: `causal`, `uplift`, `guarantee`, `proves`, `increases approvals` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

