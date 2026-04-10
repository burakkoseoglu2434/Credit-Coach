---
phase: 66
slug: demo-narrative-alignment
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-10
---

# Phase 66 — Validation Strategy

> Per-phase validation contract for deterministic actionable-vs-informational narrative posture, safe copy rules, and producer/consumer surface alignment.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + TypeScript static checks |
| **Config file** | `credit-coach/pyproject.toml`, `credit-coach-website/package.json` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_decision_explanation_pack.py -q && cd ../credit-coach-website && npm run check` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_decision_explanation_pack.py -q && cd ../credit-coach-website && npm run check && npm run build` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-local command in the plan
- **After every plan wave:** Run the quick run command
- **Before `$gsd-verify-work`:** Run the full suite command
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 66-01-01 | 01 | 1 | NARR-01, NARR-02 | unit | `cd credit-coach && python -m pytest tests/test_messaging.py -q` | ✅ | ⬜ pending |
| 66-01-02 | 01 | 1 | NARR-03 | regression | `cd credit-coach && python -m pytest tests/test_selected_surface_consistency.py -q` | ✅ | ⬜ pending |
| 66-02-01 | 02 | 2 | NARR-03 | integration | `cd credit-coach && python -m pytest tests/test_operator_packet_coherence.py -q` | ✅ | ⬜ pending |
| 66-02-02 | 02 | 2 | NARR-03 | integration | `cd credit-coach && python -m pytest tests/test_decision_explanation_pack.py -q` | ✅ | ⬜ pending |
| 66-03-01 | 03 | 3 | NARR-03 | consumer typing | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 66-03-02 | 03 | 3 | NARR-03 | consumer build | `cd credit-coach-website && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure is sufficient for Phase 66:

- [x] `credit-coach/tests/test_messaging.py` — narrative/copy contract verification
- [x] `credit-coach/tests/test_selected_surface_consistency.py` — selected projection + limited-mode empty-state guardrails
- [x] `credit-coach/tests/test_operator_packet_coherence.py` — operator packet invariants
- [x] `credit-coach/tests/test_decision_explanation_pack.py` — external-safe explanation pack + drift checks
- [x] `credit-coach-website/package.json` scripts — `check` and `build` provide typed consumer protection

---

## Manual-Only Verifications

One short manual scan is recommended after Wave 3:

- confirm Demo Center shows **band-first** recoverability posture and secondary `approval_gap` numeric
- confirm limited-mode case explicitly states “no plan promoted” and shows an informational subtype label
- confirm no surface implies guaranteed approval or causal uplift

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers producer narrative, trust surfaces, operator/external artifacts, and website consumer typing/build
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

