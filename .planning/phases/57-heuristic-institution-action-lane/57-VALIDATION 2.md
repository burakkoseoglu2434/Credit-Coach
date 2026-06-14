---
phase: 57
slug: heuristic-institution-action-lane
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-04
verified: 2026-04-04T16:52:04+03:00
---

# Phase 57 — Validation Strategy

> Per-phase validation contract for deterministic institution/hybrid candidate generation, truthful offer/approval handling, and unchanged v2.2 trust surfaces.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_heuristic_institution_lane.py tests/test_planner_quality_source_mix.py tests/test_recourse_redesign.py tests/test_messaging.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_heuristic_institution_lane.py tests/test_planner_quality_source_mix.py tests/test_recourse_redesign.py tests/test_messaging.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py tests/test_customer_artifact_collection.py tests/test_dice_lane_validity_enforcement.py -q` |
| **Estimated runtime** | ~50 seconds |

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
| 57-01-01 | 01 | 1 | INST-01, INST-03 | generation contract | `cd credit-coach && python -m pytest tests/test_heuristic_institution_lane.py -q` | ✅ | ✅ green |
| 57-01-02 | 01 | 1 | INST-01, INST-02, INST-03 | canonical builder / offer contract integration | `cd credit-coach && python -m pytest tests/test_heuristic_institution_lane.py tests/test_recourse_redesign.py -q` | ✅ | ✅ green |
| 57-02-01 | 02 | 2 | INST-02, INST-03, INST-04 | contender gating / pool integration | `cd credit-coach && python -m pytest tests/test_heuristic_institution_lane.py tests/test_planner_quality_source_mix.py tests/test_recourse_redesign.py -q` | ✅ | ✅ green |
| 57-02-02 | 02 | 2 | INST-03, INST-04 | approval-shell and offer-maturity truth | `cd credit-coach && python -m pytest tests/test_heuristic_institution_lane.py tests/test_planner_quality_source_mix.py tests/test_customer_artifact_collection.py -q` | ✅ | ✅ green |
| 57-03-01 | 03 | 3 | INST-03, INST-04 | customer/operator rendering | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py -q` | ✅ | ✅ green |
| 57-03-02 | 03 | 3 | INST-04 | trust regression / artifact parity | `cd credit-coach && python -m pytest tests/test_winner_integrity_hard_stop.py tests/test_customer_artifact_collection.py tests/test_dice_lane_validity_enforcement.py tests/test_recourse_redesign.py -q` | ✅ | ✅ green |

*Status: ⬜ planned · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covered the phase requirements, and the new focused suite `tests/test_heuristic_institution_lane.py` is now in place and green.*

---

## Manual-Only Verifications

One human scan is still useful after execution:

- confirm institution-side recommendations never read as guaranteed approvals when the offer is provisional or pending
- confirm approval-shell-only candidates remain visible diagnostically but do not silently displace actionable winners
- confirm selected customer surfaces still separate `primary_recommendation` from `institution_condition`
- confirm DICE candidates are unaffected by the new heuristic lane except for coexistence in the shared pool

All hard trust and contention gates should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all referenced suites
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** execution verified 2026-04-04
