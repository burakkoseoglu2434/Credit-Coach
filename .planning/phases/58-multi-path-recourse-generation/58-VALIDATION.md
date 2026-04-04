---
phase: 58
slug: multi-path-recourse-generation
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-04
verified: 2026-04-04T17:34:18+03:00
---

# Phase 58 - Validation Strategy

> Per-phase validation contract for deterministic multi-path grouping, duplicate-resistant path identity, and unchanged trust surfaces.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recourse_paths.py tests/test_customer_artifact_collection.py tests/test_batch_candidate_diversity.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_recourse_paths.py tests/test_customer_artifact_collection.py tests/test_batch_candidate_diversity.py tests/test_planner_quality_source_mix.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py tests/test_dice_lane_validity_enforcement.py -q` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_recourse_paths.py tests/test_customer_artifact_collection.py tests/test_batch_candidate_diversity.py -q`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_recourse_paths.py tests/test_customer_artifact_collection.py tests/test_batch_candidate_diversity.py tests/test_planner_quality_source_mix.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py tests/test_dice_lane_validity_enforcement.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 58-01-01 | 01 | 1 | PATH-01 | unit | `cd credit-coach && python -m pytest tests/test_recourse_paths.py -q` | ✅ | ✅ green |
| 58-01-02 | 01 | 1 | PATH-02 | unit | `cd credit-coach && python -m pytest tests/test_recourse_paths.py tests/test_planner_quality_source_mix.py -q` | ✅ | ✅ green |
| 58-02-01 | 02 | 2 | PATH-01 | integration | `cd credit-coach && python -m pytest tests/test_recourse_paths.py tests/test_customer_artifact_collection.py -q` | ✅ | ✅ green |
| 58-02-02 | 02 | 2 | PATH-03 | integration | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_customer_artifact_collection.py -q` | ✅ | ✅ green |
| 58-03-01 | 03 | 3 | PATH-02 | regression | `cd credit-coach && python -m pytest tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py -q` | ✅ | ✅ green |
| 58-03-02 | 03 | 3 | PATH-03 | regression | `cd credit-coach && python -m pytest tests/test_recourse_paths.py tests/test_batch_candidate_diversity.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py tests/test_dice_lane_validity_enforcement.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recourse_paths.py` - focused path typing, grouping, dedupe, and representative-selection tests are in place and green

*Existing infrastructure covers all other phase requirements and trust regressions.*

---

## Manual-Only Verifications

All phase behaviors have automated verification. One useful manual read is to confirm selected-path fields remain additive in customer artifacts rather than replacing selected-plan truth.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all referenced suites
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** execution verified 2026-04-04
