---
phase: 52-preferred-policy-baseline-demo-proof
plan: 03
subsystem: regression-and-cohort-proof
tags: [regression, rerun, cohorts, evidence, demo-proof]
requires: [52-01, 52-02]
provides:
  - regression-closed Phase 52 package
  - three-cohort preferred-baseline proof
  - honest next-step handoff
affects: [phase-52, regressions, rerun-proof, milestone-closeout]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py
    - credit-coach/tests/test_decision_calibration.py
    - credit-coach/tests/test_customer_artifact_collection.py
    - credit-coach/tests/test_pilot_baseline_refresh.py
    - credit-coach/tests/test_pilot_artifact_qa.py
key-decisions:
  - "Phase 52 closes on deterministic proof that the shipped baseline remains preferred, not on manufactured uplift."
  - "Three standard cohorts remain the required evidence surface for the milestone-close package."
patterns-established:
  - "v2.3 can now close with honest preferred-baseline packaging, explicit candidate non-adoption, and a bounded next-step story."
requirements-completed: [POL-01, POL-02]
duration: manual-execution
completed: 2026-04-03
---

# Phase 52 Plan 03 Summary

**Phase 52 closed with replayable proof that the shipped runtime baseline remains the honest demo and pilot baseline.**

## Accomplishments

- Ran the full Phase 52 regression suite and confirmed the baseline-selection package coexists with existing calibration, collection, pilot refresh, QA, experiment-suite, and funnel KPI seams.
- Re-ran the three deterministic 250-customer standard cohorts:
  - `pilot_mixed` → `20260403_143938_842569_f7b04b`
  - `risk_band_balanced` → `20260403_144133_ad71f7_a1b81f`
  - `offer_needed_balanced` → `20260403_144416_c7f6b6_ca95d9`
- Confirmed the same Phase 52 posture in all three cohort manifests:
  - runtime policy version = `v2.1_phase_40_5`
  - preferred demo profile = `preferred_demo_baseline_v2_3`
  - fallback demo profile = `trust_first_baseline_v2_3`
  - threshold family status = `no_safe_uplift`
  - outcome-rule family status = `no_safe_uplift`
  - next milestone focus = `expand_movement_levers`
- Confirmed the same cohort-level bottleneck story from the new baseline-selection artifact:
  - dominant movement bottleneck = `structural_cohort_limited`
  - no candidate family created promotable movement under shipped trust and risk guardrails
  - candidate disposition count = `6`
- Cleaned up the collection concat path and verified a follow-up `pilot_mixed` rerun (`20260403_151804_842569_ad8a77`) completes without the pandas concat `FutureWarning`.

## Verification

- `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_phase_experiment_suite.py tests/test_recourse_funnel_kpis.py -q`
- `cd credit-coach && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy pilot_mixed`
- `cd credit-coach && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy risk_band_balanced`
- `cd credit-coach && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy offer_needed_balanced`

## Notes

- Phase 52 proves honest selection and honest non-selection; it does not claim bounded policy uplift.
- The next milestone can now focus on expanding movement levers instead of relitigating threshold-only or offer/readiness-only candidates.

---
*Phase: 52-preferred-policy-baseline-demo-proof*
*Completed: 2026-04-03*
