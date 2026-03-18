---
phase: 18
slug: decision-narrative-product-output-translation
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-18
---

# Phase 18 - Validation Strategy

> Per-phase validation contract for engine-owned narrative translation, controlled technical reveal, and shared UI-ready output schema.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + TypeScript build checks |
| **Config file** | `credit-coach/pyproject.toml`, `credit-coach-website/tsconfig.json`, `credit-coach-website/tsconfig.node.json` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_policy_engine.py tests/test_recourse_redesign.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_policy_engine.py tests/test_recourse_redesign.py tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py && cd ../credit-coach-website && npm run check && npm run build` |
| **Estimated runtime** | ~65 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_policy_engine.py tests/test_recourse_redesign.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_policy_engine.py tests/test_recourse_redesign.py tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py`
- **Before `$gsd-verify-work`:** Full suite must be green, including `credit-coach-website` `check` and `build`
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | PORT-02 | narrative schema and serialization | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_messaging.py` | ✅ | ⬜ pending |
| 18-01-02 | 01 | 1 | PORT-02 | action template and executive summary determinism | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_policy_engine.py` | ✅ | ⬜ pending |
| 18-02-01 | 02 | 2 | PORT-02 | checkpoint, offer, reason, and confidence narrative layers | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_policy_engine.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 18-02-02 | 02 | 2 | PORT-02 | technical reveal integrity and vocabulary consistency | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_phase_experiment_suite.py` | ✅ | ⬜ pending |
| 18-03-01 | 03 | 3 | PORT-02 | shared schema compatibility across engine and website | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 18-03-02 | 03 | 3 | PORT-02 | renderability of one artifact across website and analyst views | `cd credit-coach-website && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_messaging.py` - extend the existing human-readable reason seam rather than inventing a new one
- [x] `credit-coach/tests/test_policy_engine.py` - protect adverse-action payload compatibility with policy outputs
- [x] `credit-coach/tests/test_recourse_redesign.py` - protect serialized roadmap shape and action/trajectory output seams
- [x] `credit-coach/tests/test_phase_experiment_suite.py` - verify downstream artifact consumption stays stable when the roadmap contract gains a narrative layer
- [x] `credit-coach/tests/test_portfolio_validation.py` - keep product-ready and reality-gap assumptions compatible with the new narrative contract
- [x] `credit-coach-website/package.json` scripts - existing `check` and `build` are sufficient for consumer validation

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm the default roadmap view answers in plain product language:
  - what is happening
  - what should the customer do
  - why it matters
  - what to expect at the next checkpoint
- confirm raw feature deltas do not appear in the default business-first view
- confirm technical detail is still available through controlled reveal rather than being silently removed
- confirm offer narration is clearly separate from ordinary action narration
- confirm adverse-action reasons read like institution-safe explanation text rather than code dumps
- confirm `high / moderate / low` confidence labels make sense and do not overclaim certainty
- confirm the same underlying artifact can support both a lean website rendering and a richer analyst rendering
- confirm TR and EN phrasing remain semantically aligned and deterministic
- confirm the website no longer depends on hidden business logic to translate raw engine output into product narrative

All core behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers engine narrative, reason translation, roadmap serialization, downstream artifact consumption, and website schema consumption
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-18
