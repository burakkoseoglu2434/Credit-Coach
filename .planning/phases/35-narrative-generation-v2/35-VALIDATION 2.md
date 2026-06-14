---
phase: 35
slug: narrative-generation-v2
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-22
---

# Phase 35 - Validation Strategy

> Per-phase validation contract for personalized, product-ready narrative generation on top of hardened semantic, numeric, feasibility, execution, and offer truth.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_recourse_redesign.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_recourse_redesign.py tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_recourse_redesign.py`
- **After every plan wave:** Run the wave-local verification command listed below
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 35-01-01 | 01 | 1 | NARV-01 | narrative contract ordering and step/checkpoint composition | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_messaging.py` | ✅ | ⬜ pending |
| 35-01-02 | 01 | 1 | NARV-01 | primary numeric placement plus step realism cues | `cd credit-coach && python -m pytest tests/test_messaging.py` | ✅ | ⬜ pending |
| 35-02-01 | 02 | 2 | NARV-01 | personalization posture and behavior-led wording | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 35-02-02 | 02 | 2 | NARV-01 | tone, offer-companion posture, and default reason curation | `cd credit-coach && python -m pytest tests/test_messaging.py` | ✅ | ⬜ pending |
| 35-03-01 | 03 | 3 | NARV-01 | business-vs-technical narrative split and technical reveal completeness | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 35-03-02 | 03 | 3 | NARV-01 | runtime artifact stability and downstream consumer regression closure | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_messaging.py` — existing narrative, checkpoint, reason, and offer wording seams already protect deterministic output
- [x] `credit-coach/tests/test_recourse_redesign.py` — roadmap serialization tests already protect the sibling narrative branch
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — downstream artifact consumers already exist to catch serialization regressions
- [x] `credit-coach/tests/test_portfolio_validation.py` — proof-facing consumers already validate stability around narrative-related artifact structure

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm the default roadmap story reads in this order:
  - what is happening
  - what the customer should do
  - what to expect at checkpoints
  - why the plan exists
- confirm each step shows one primary numeric statement rather than multiple competing metrics
- confirm feasibility and difficulty cues stay compact rather than becoming explanation dumps
- confirm the copy feels personalized through current state, target, and timing rather than through generic persona writing
- confirm offer-bearing plans still read as customer-path-first rather than offer-first
- confirm default narrative never exposes raw probabilities
- confirm top reasons remain short and action-oriented in default view while full reason detail stays recoverable technically
- confirm tone stays calm, confident, gently directive, and non-threatening in both positive and negative outcome wording

All core behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers engine narrative, runtime serialization, and downstream artifact consumers
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-22
