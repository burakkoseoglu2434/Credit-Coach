---
phase: 43
slug: operator-review-pack
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-23
---

# Phase 43 — Validation Strategy

> Per-phase validation contract for per-customer operator packets, collection-level operator briefings, business-safe three-state review surfaces, and appendix-safe traceability.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_operator_review_pack.py tests/test_customer_artifact_collection.py tests/test_messaging.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_operator_review_pack.py tests/test_customer_artifact_collection.py tests/test_messaging.py tests/test_recourse_redesign.py tests/test_decision_calibration.py -q` |
| **Estimated runtime** | ~40 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-local command in the plan
- **After every plan wave:** Run the quick run command
- **Before `$gsd-verify-work`:** Run the full suite command
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 43-01-01 | 01 | 1 | OPS-01 | packet schema and per-customer derivation | `cd credit-coach && python -m pytest tests/test_operator_review_pack.py -q` | ❌ W0 | ⬜ pending |
| 43-01-02 | 01 | 1 | OPS-01 | messaging-safe summary, blockers, and actions integration | `cd credit-coach && python -m pytest tests/test_operator_review_pack.py tests/test_messaging.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 43-02-01 | 02 | 2 | OPS-02 | collection briefing aggregation and queue guidance | `cd credit-coach && python -m pytest tests/test_operator_review_pack.py tests/test_customer_artifact_collection.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 43-02-02 | 02 | 2 | OPS-02 | calibration-fed operator-safe hotspot and health-note coverage | `cd credit-coach && python -m pytest tests/test_operator_review_pack.py tests/test_customer_artifact_collection.py tests/test_decision_calibration.py -q` | ❌ W0 / ✅ / ✅ | ⬜ pending |
| 43-03-01 | 03 | 3 | OPS-01, OPS-02 | operator packet write paths and collection summary packaging | `cd credit-coach && python -m pytest tests/test_operator_review_pack.py tests/test_customer_artifact_collection.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 43-03-02 | 03 | 3 | OPS-01, OPS-02 | integrated regression and business-safe leak guard | `cd credit-coach && python -m pytest tests/test_operator_review_pack.py tests/test_customer_artifact_collection.py tests/test_messaging.py tests/test_recourse_redesign.py tests/test_decision_calibration.py -q` | ❌ W0 / ✅ / ✅ / ✅ / ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `credit-coach/tests/test_operator_review_pack.py` — new dedicated test module for packet contract, blocker/action tracing, business-safe leak guards, and collection briefing sections
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect additive artifact wiring and summary/manifest expansion
- [x] `credit-coach/tests/test_messaging.py` — existing messaging tests can protect business-safe phrasing and technical appendix boundaries
- [x] `credit-coach/tests/test_decision_calibration.py` — existing calibration tests can protect operator-safe consumption of funnel and hotspot signals
- [x] `credit-coach/tests/test_recourse_redesign.py` — existing roadmap tests can protect raw truth ownership remaining unchanged

---

## Manual-Only Verifications

One human scan is still recommended after execution:

- confirm `operator_packet.json` is a derived view of existing truth rather than a new decision source
- confirm `operator_packet.md` is readable without opening raw technical artifacts
- confirm every non-approved packet says both why the decision is not approved and what would upgrade it
- confirm `NEEDS_REVIEW` never appears as a user-facing decision state in packet short view or collection briefing
- confirm collection briefing feels prioritization-oriented rather than like a tuning dashboard

All core packet and briefing rules should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers the only missing test seam
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-23
