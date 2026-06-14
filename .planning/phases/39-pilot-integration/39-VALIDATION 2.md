---
phase: 39
slug: pilot-integration
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-22
---

# Phase 39 - Validation Strategy

> Per-phase validation contract for institution-style pilot intake, engine-owned pilot package emission, pilot guardrail packaging, and operator-facing onboarding honesty.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + shell docs guards |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_pilot_integration.py tests/test_release_decision.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_pilot_integration.py tests/test_release_decision.py tests/test_production_smoke.py tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_pilot_integration.py tests/test_release_decision.py -q`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_pilot_integration.py tests/test_release_decision.py tests/test_production_smoke.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green and pilot docs must match the emitted package contract
- **Max feedback latency:** 35 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 39-01-01 | 01 | 1 | PILT-01 | typed pilot input contract and mapping validation | `cd credit-coach && python -m pytest tests/test_pilot_integration.py -q` | ✅ | ⬜ pending |
| 39-01-02 | 01 | 1 | PILT-01 | manifest and provenance-safe pilot intake packaging | `cd credit-coach && python -m pytest tests/test_pilot_integration.py tests/test_portfolio_validation.py -q` | ✅ | ⬜ pending |
| 39-02-01 | 02 | 2 | PILT-01 | end-to-end pilot package runner | `cd credit-coach && python -m pytest tests/test_pilot_integration.py tests/test_release_decision.py -q` | ✅ | ⬜ pending |
| 39-02-02 | 02 | 2 | PILT-01 | pilot guardrails, acceptance status, and smoke-safe packaging | `cd credit-coach && python -m pytest tests/test_release_decision.py tests/test_production_smoke.py tests/test_phase_experiment_suite.py -q` | ✅ | ⬜ pending |
| 39-03-01 | 03 | 3 | PILT-01 | pilot onboarding and package-doc completeness | `rg -n "run_pilot_integration|pilot_package_manifest|pilot_guardrails|portfolio_validation_summary|product_confidence_snapshot" credit-coach/docs/PILOT_DATA_CONTRACT.md credit-coach/docs/PILOT_EXECUTION_GUIDE.md credit-coach-website/PILOT_READINESS.md credit-coach-website/CURATED_DEMO_HANDOFF.md` | ✅ | ⬜ pending |
| 39-03-02 | 03 | 3 | PILT-01 | regression closure for pilot seam and portfolio truth reuse | `cd credit-coach && python -m pytest tests/test_pilot_integration.py tests/test_release_decision.py tests/test_production_smoke.py tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py` - existing batch runner can remain the planning core underneath pilot packaging
- [x] `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py` - existing guardrail and proof packaging can be reused rather than recreated
- [x] `credit-coach/src/credit_coach/ops/release_decision.py` - pilot eligibility and guardrail semantics already exist
- [x] `credit-coach/src/credit_coach/ops/kpi_contract.py` - acceptance status and milestone-facing pilot wording already exist
- [x] `credit-coach-website/PILOT_READINESS.md` - current controlled pilot posture is already documented
- [x] `credit-coach-website/CURATED_DEMO_HANDOFF.md` - current operator handoff seam is already documented

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm the pilot seam stays artifact-first and does not claim live external integration
- confirm the institution-style input contract fails closed on missing mandatory fields
- confirm the emitted pilot package points to engine-owned artifacts rather than website-invented summaries
- confirm pilot eligibility and watchlist posture remain explicit even when the result is only `PILOT_ONLY`
- confirm onboarding docs distinguish controlled pilot scope from deferred auth, CRM, or real-time integration work

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity preserved across all three execution waves
- [x] Wave 0 covers the existing engine, guardrail, and website pilot seams reused by Phase 39
- [x] No watch-mode flags
- [x] Feedback latency acceptable for iterative execution
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-22
