# Phase 8: Fairness Stability Matrix - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the fairness-stability evidence needed to understand and control seeded regressions in the existing Credit Coach release pipeline. This phase clarifies how seeded fairness failures are measured, localized, classified into release decisions, and packaged into actionable evidence; it does not add new end-user capabilities.

</domain>

<decisions>
## Implementation Decisions

### Release Decision Contract
- Release decisions must be deterministic and evaluated in this order:
  - `reliability_pass == false` -> `NO_GO`
  - `lift_pass == false` -> `NO_GO`
  - otherwise run the fairness-based release decision logic
- `GO` requires:
  - `lift_pass == true`
  - `reliability_pass == true`
  - `fairness_seed_pass_count == fairness_seed_total`
- `LIMITED_GO` is only allowed when:
  - `lift_pass == true`
  - `reliability_pass == true`
  - `fairness_seed_pass_count == fairness_seed_total - 1`
  - `dominant_fail_segment_share >= 0.60`
  - worst primary fairness gap is `<= fairness_threshold * 1.5`
  - supporting guardrails are not in a catastrophic state
- `NO_GO` applies when:
  - `fairness_seed_pass_count <= fairness_seed_total - 2`
  - or failure concentration is not localized
  - or fairness magnitude exceeds the allowed `LIMITED_GO` cap

### Fairness Contract Metrics
- The primary fairness threshold is `equalized_odds_gap_delta`
- Supporting hard guardrails are:
  - `high_stress_fairness_gap_after`
  - `recourse_success_gap`
- `approval_gap_delta` and `fairness_gap_after` remain secondary diagnostic metrics and should be reported, but they do not define seed pass/fail on their own
- A seed counts as fairness `PASS` only if:
  - `equalized_odds_gap_delta <= threshold_primary`
  - `high_stress_fairness_gap_after <= threshold_high_stress`
  - `recourse_success_gap <= threshold_recourse_success`

### Breakdown Depth
- Default fairness breakdowns must always include:
  - `seed x segment`
  - `segment x candidate source`
  - `high-stress scenario x segment`
  - `seed x primary_fail_reason`
- A summary rollup must also include:
  - `risk band x source`
- The purpose of the default package is to expose seed-localized failures, source-localized failures, high-stress segment failures, and fail-reason concentration without turning the phase into a general dashboard effort

### Segment Catalog
- `dominant_fail_segment_key` must come from one unified canonical segment catalog
- The canonical segment space must combine business/risk and fairness-relevant dimensions rather than using a fairness-only or business-only segment definition
- Minimum dimensions for the canonical segment key:
  - `risk_band`
  - `income_band` or `income_quantile`
  - `stress_band` or `high_stress_flag`
- `candidate_source` should be reported as a companion field when possible:
  - e.g. `dominant_fail_segment_key = "mid|q1|stress"`
  - e.g. `dominant_fail_candidate_source = "internal"`
- Only fuse `candidate_source` into the segment key if the existing artifact schema makes separation impractical

### Failure Semantics
- `LIMITED_GO` is not just a label; it must activate a default operational restriction package
- If `release_decision == LIMITED_GO`, the system must emit:
  - `smoke_pass = false`
  - `pilot_eligible = true`
  - `broad_rollout_allowed = false`
  - `max_traffic_pct = 5`
  - `fairness_monitoring_required = true`
  - `rollback_guard_required = true`
  - `targeted_alerting_required = true`
  - `manual_approval_required = true`
  - `remediation_artifacts_required = true`
- `LIMITED_GO` means pilot-eligible only; it must never count as broad production readiness
- Default rollback triggers for `LIMITED_GO`:
  - `reliability_pass` becomes false
  - `equalized_odds_gap_delta` exceeds the `LIMITED_GO` cap
  - `high_stress_fairness_gap_after` exceeds a hard cap
  - `recourse_success_gap` exceeds a hard cap
  - `dominant_fail_segment_share < 0.60`
  - traffic exceeds the configured pilot limit

### Evidence Format
- Phase 8 evidence must be dual-output:
  - machine-readable artifacts are the canonical source of truth
  - a concise human-readable release review summary is generated as a derived companion artifact
- Canonical artifacts must include:
  - `release_decision.json`
  - `phase_scale_seed_summary.csv`
  - `phase_scale_aggregate.json`
  - `fairness_failure_breakdown.csv`
- Companion artifacts for pilot/remediation behavior should be emitted when applicable:
  - `pilot_guardrails.json`
  - `rollback_conditions.json`
- The human-readable derived artifact should summarize:
  - `GO | LIMITED_GO | NO_GO`
  - fail reason
  - fairness seed pass count
  - dominant fail segment
  - dominant fail candidate source
  - worst fairness gap
  - the active `LIMITED_GO` operational package

### Claude's Discretion
- Exact JSON field naming for non-canonical helper metadata as long as the locked decision fields remain explicit
- Whether `pilot_guardrails.json` and `rollback_conditions.json` are always written or conditionally written when `LIMITED_GO` / `NO_GO` applies, as long as remediation artifacts are preserved
- Exact Markdown structure of the human-readable summary file as long as it is derived from the canonical artifacts

</decisions>

<specifics>
## Specific Ideas

- `run_production_smoke.py` should expose a three-valued decision field: `GO | LIMITED_GO | NO_GO`
- `smoke_pass` should be `true` only for `GO`
- `pilot_eligible` should be `true` only for `LIMITED_GO`
- Suggested function shape: `evaluate_release_decision(metrics) -> GO | LIMITED_GO | NO_GO`
- The phase should make seeded KPI runs actionable diagnostics rather than noisy aggregates

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/evaluation/fairness.py`: already contains composite-group builders, multi-segment fairness summaries, fairness bundles, and high-stress matrix helpers that can ground seeded breakdown outputs
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`: already produces seeded suite artifacts, contains `_kpi_checks(...)`, and supports deterministic `train_once` behavior via `--skip_train_before_batch`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`: already computes aggregate variant metrics and gate-violation ranking logic, making it a natural hook point for the shared release decision contract
- `credit-coach/src/credit_coach/cli/run_production_smoke.py`: already builds gate rows from artifact packs and can carry new release decision metadata
- `credit-coach/tests/test_phase_experiment_suite.py` and `credit-coach/tests/test_production_smoke.py`: existing contract-style tests can be extended to lock seeded fairness semantics and smoke metadata

### Established Patterns
- Artifact-first execution: the system writes JSON/CSV evidence under `artifacts/runs/<run_id>/tables/`
- Config-first contract behavior: thresholds already live in YAML and are consumed by multiple runners
- Flat pytest functions plus pandas-based assertions are the established way to test KPI contract behavior

### Integration Points
- Phase 8 changes must hook into:
  - `run_phase_experiment_suite.py`
  - `run_model_challenger_matrix.py`
  - `run_production_smoke.py`
- Shared fairness helpers in `evaluation/fairness.py` should own as much of the breakdown logic as possible to reduce runner drift
- New artifacts should follow the existing `artifacts/runs/<run_id>/tables/` evidence layout

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---
*Phase: 08-fairness-stability-matrix*
*Context gathered: 2026-03-14*
