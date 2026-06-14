---
phase: 60
slug: validation-cohort-evaluation
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-04
verified: 2026-04-05T00:25:00+03:00
---

# Phase 60 - Validation Strategy

> Per-phase validation contract for cohort-evidence assembly, movement-diagnosis integrity, and unchanged v2.2 trust surfaces.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_batch_candidate_diversity.py tests/test_customer_artifact_collection.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_batch_candidate_diversity.py tests/test_customer_artifact_collection.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py tests/test_dice_lane_validity_enforcement.py -q` |
| **Estimated runtime** | ~35 seconds |

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
| 60-01-01 | 01 | 1 | EVAL-01 | unit | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ✅ green |
| 60-01-02 | 01 | 1 | EVAL-01, EVAL-02 | integration | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_batch_candidate_diversity.py -q` | ✅ | ✅ green |
| 60-02-01 | 02 | 2 | EVAL-01, EVAL-02 | integration | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_customer_artifact_collection.py -q` | ✅ | ✅ green |
| 60-02-02 | 02 | 2 | EVAL-01 | integration | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_batch_candidate_diversity.py tests/test_customer_artifact_collection.py -q` | ✅ | ✅ green |
| 60-03-01 | 03 | 3 | EVAL-02, EVAL-03 | regression | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_customer_artifact_collection.py -q` | ✅ | ✅ green |
| 60-03-02 | 03 | 3 | EVAL-03 | regression | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_batch_candidate_diversity.py tests/test_customer_artifact_collection.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py tests/test_dice_lane_validity_enforcement.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_cohort_evaluation.py` - focused Phase 60 evidence-assembly and table-contract proof

*Existing infrastructure covers the trust-regression suites and batch/customer artifact flows.*

---

## Manual-Only Verifications

- confirm the final Markdown evaluation summary answers whether movement improved, whether `structural_cohort_limited` softened or remained dominant, and whether trust stayed intact
- confirm trust-regression reporting appears side-by-side with cohort tables so higher path diversity cannot be misread as safe movement by itself

All hard evidence and trust invariants should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths or Wave 0 coverage
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** execution verified 2026-04-05
