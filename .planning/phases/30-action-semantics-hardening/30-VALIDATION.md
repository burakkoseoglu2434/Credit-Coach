---
phase: 30
slug: action-semantics-hardening
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-20
---

# Phase 30 - Validation Strategy

> Per-phase validation contract for locked action taxonomy, deterministic grouped semantics, product-safe serialization identity, and explicit business-vs-technical action views.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py tests/test_messaging.py tests/test_batch_candidate_diversity.py` |
| **Estimated runtime** | ~35 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_action_space.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 30-01-01 | 01 | 1 | ACT-01 | catalog/taxonomy | `cd credit-coach && python -m pytest tests/test_action_space.py` | ✅ | ⬜ pending |
| 30-01-02 | 01 | 1 | ACT-01 | mapping hard-fail | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 30-02-01 | 02 | 2 | ACT-01 | grouped identity | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 30-02-02 | 02 | 2 | ACT-01 | serialization/schema | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_messaging.py` | ✅ | ⬜ pending |
| 30-03-01 | 03 | 3 | ACT-01 | narrative separation | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 30-03-02 | 03 | 3 | ACT-01 | downstream artifact compatibility | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_messaging.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_action_space.py` — existing catalog and grouping tests can protect taxonomy, `action_family`, and deterministic group identity
- [x] `credit-coach/tests/test_recourse_redesign.py` — existing roadmap and action-contract tests can protect grouped semantic output and no-raw-feature default behavior
- [x] `credit-coach/tests/test_messaging.py` — existing narrative tests can protect business-first defaults and `technical_reveal` containment
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` — existing downstream artifact tests can protect batch-facing compatibility for grouped semantics

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm no main recommendation is readable as a raw feature name by default
- confirm `action_family` is stable and business-meaningful across behavioral, structural, and institutional actions
- confirm same-primary-action effects collapse into one grouped default action per phase
- confirm grouped actions do not cross action classes
- confirm `feature_name` remains available only in technical or effect-facing views
- confirm `business_view` and `technical_view` are explicit in the engine-owned schema rather than implied by frontend naming
- confirm titles and short descriptions are deterministic and catalog-driven rather than runtime improvisation

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers taxonomy, roadmap contract, messaging, and downstream artifact seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-20
