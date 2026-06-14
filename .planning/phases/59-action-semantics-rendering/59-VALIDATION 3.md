---
phase: 59
slug: action-semantics-rendering
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-04
---

# Phase 59 - Validation Strategy

> Per-phase validation contract for deterministic action and path rendering, selected-projection alignment, and unchanged trust surfaces.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recourse_rendering.py tests/test_messaging.py tests/test_customer_artifact_collection.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_recourse_rendering.py tests/test_messaging.py tests/test_recourse_redesign.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_customer_artifact_collection.py tests/test_winner_integrity_hard_stop.py -q` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_recourse_rendering.py tests/test_messaging.py tests/test_customer_artifact_collection.py -q`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_recourse_rendering.py tests/test_messaging.py tests/test_recourse_redesign.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_customer_artifact_collection.py tests/test_winner_integrity_hard_stop.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 59-01-01 | 01 | 1 | REND-01 | unit | `cd credit-coach && python -m pytest tests/test_recourse_rendering.py -q` | ❌ W0 | ⬜ pending |
| 59-01-02 | 01 | 1 | REND-01, REND-02 | unit | `cd credit-coach && python -m pytest tests/test_recourse_rendering.py tests/test_messaging.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 59-02-01 | 02 | 2 | REND-01, REND-03 | integration | `cd credit-coach && python -m pytest tests/test_recourse_rendering.py tests/test_recourse_redesign.py tests/test_customer_artifact_collection.py -q` | ❌ W0 / ✅ / ✅ | ⬜ pending |
| 59-02-02 | 02 | 2 | REND-03 | integration | `cd credit-coach && python -m pytest tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_customer_artifact_collection.py -q` | ✅ | ⬜ pending |
| 59-03-01 | 03 | 3 | REND-02 | regression | `cd credit-coach && python -m pytest tests/test_recourse_rendering.py tests/test_messaging.py tests/test_selected_surface_consistency.py -q` | ❌ W0 / ✅ / ✅ | ⬜ pending |
| 59-03-02 | 03 | 3 | REND-03 | regression | `cd credit-coach && python -m pytest tests/test_recourse_rendering.py tests/test_messaging.py tests/test_recourse_redesign.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_customer_artifact_collection.py tests/test_winner_integrity_hard_stop.py -q` | ❌ W0 / ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `credit-coach/tests/test_recourse_rendering.py` - focused action and path render tests for metric phrasing, dependency honesty, weak-language suppression, and path-summary serialization

*Existing infrastructure covers all other phase requirements and trust regressions.*

---

## Manual-Only Verifications

One brief manual read is still useful after execution:

- confirm customer-facing path summaries stay concise and non-jargon while operator-facing summaries remain more explicit without changing meaning

All hard trust and rendering invariants should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all referenced suites
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
