# Phase 11: Release Evidence and Outcome Feedback - Context

**Gathered:** 2026-03-15
**Status:** Ready for replanning

<domain>
## Phase Boundary

Make production-like release evidence complete, reproducible, and connected to business-impact proxies. This phase clarifies how telemetry health constrains rollout semantics, how release evidence packs are organized, how outcome-feedback comparisons are interpreted, and what the review surface should emphasize. It does not replace the Phase 8 release contract, the Phase 9 acceptance contract, or the Phase 10 explanation-first review principle.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 8-10
- Phase 8 release semantics remain authoritative:
  - `reliability_pass == false` -> `NO_GO`
  - `lift_pass == false` -> `NO_GO`
  - otherwise evaluate fairness-driven `GO | LIMITED_GO | NO_GO`
- Phase 9 acceptance semantics remain authoritative:
  - repeated seeded evidence is still the basis for acceptance eligibility
  - degraded evidence may emit operational signals but does not become acceptance-grade
- Phase 10 review philosophy remains authoritative:
  - machine-readable artifacts are the canonical source of truth
  - markdown review is always derived and explanation-first rather than a dashboard
- Phase 11 is additive to those contracts; it does not define a second acceptance path

### Telemetry Gate Behavior
- `release_decision` should still be computed from the existing KPI, reliability, lift, and fairness contract even when telemetry is missing or degraded
- Telemetry must be applied as a separate operational gate
- If telemetry is missing or degraded:
  - `broad_rollout_allowed = false`
  - `smoke_pass = false`
- Telemetry health is also required for pilot operation
- If `release_decision == LIMITED_GO` but telemetry is degraded:
  - `pilot_eligible = false`
  - `broad_rollout_allowed = false`
  - `smoke_pass = false`
- Canonical telemetry failure reasons are:
  - `missing_artifact`
  - `disabled_exporter`
  - `export_failed`
  - `success_rate_below_threshold`
  - `ingest_lag_above_threshold`
- Canonical telemetry fields that must be present in machine-readable outputs are:
  - `telemetry_status`
  - `telemetry_gate_status`
  - `telemetry_failure_reason`
  - `telemetry_success_rate`
  - `telemetry_ingest_lag_s`
  - `telemetry_required_for_broad_rollout`
- Strongly preferred additional telemetry fields are:
  - `telemetry_required_for_pilot`
  - `telemetry_artifact_path`

### Release Pack Contract
- Canonical ownership of the release evidence pack belongs to the seeded suite runner:
  - `run_phase_experiment_suite.py` should emit the milestone-level canonical `release_evidence_pack.json`
- Smoke and challenger may emit compatible local evidence snapshots, but they are not the milestone-level source of truth
- Paths inside the release pack should use `tables/`-relative artifact references rather than absolute filesystem paths
- The minimum release-pack artifact set is:
  - `kpi_contract_snapshot.json`
  - `milestone_acceptance_summary.json`
  - `phase_scale_seed_summary.csv`
  - `phase_scale_aggregate.json`
  - `fairness_failure_breakdown.csv`
  - `candidate_quality_summary.json`
  - `candidate_source_breakdown.csv`
  - `telemetry_export.json`
  - `milestone_acceptance_review.md`
- Strongly preferred additional release-pack artifact:
  - `release_decision.json`
- The release pack must always be written, even when evidence is incomplete
- Release-pack completeness must be explicit via:
  - `pack_status = complete | degraded`
  - `missing_artifacts`
  - `required_artifacts`
  - `optional_artifacts`
  - `pack_acceptance_eligible`
- Strongly preferred additional pack metadata:
  - `pack_generated_at`
  - `pack_root`

### Outcome Feedback Comparison Policy
- Primary outcome-feedback comparison language is:
  - `treatment vs control`
- If multiple non-control policy arms exist:
  - machine-readable artifacts should report each arm relative to control
  - the derived review should summarize only:
    - `best proxy-improving arm`
    - `worst proxy-regressing arm`
- If the control arm is missing:
  - reports should still be written
  - `comparison_status = baseline_missing`
  - `outcome_feedback_confidence = tentative`
  - direct comparative delta claims should not be made
  - the report should fall back to descriptive per-arm summaries
- Canonical business-impact proxy set is:
  - `approval_rate`
  - `default_rate_90d`
  - `avg_margin_90d`
- Outcome-feedback remains comparative and proxy-oriented, not causal
- Outcome-feedback evidence remains companion evidence and must not replace the primary seeded acceptance contract

### Review Surface
- Phase 11 review remains explanation-first rather than dashboard-like
- Default review section order is:
  - `Decision`
  - `Telemetry Readiness`
  - `Release Pack Completeness`
  - `Outcome Feedback Summary`
  - `Supporting Artifacts`
- At the top of the review, include a concise evidence-status line:
  - `Evidence Status = complete | degraded`
  - include the primary reason such as:
    - `missing_artifacts`
    - `baseline_missing`
    - `telemetry_degraded`
- `Telemetry Readiness` should show only the core operational readiness fields:
  - `telemetry_gate_status`
  - `telemetry_failure_reason`
  - `telemetry_success_rate`
  - `telemetry_ingest_lag_s`
  - `broad_rollout_allowed`
  - `pilot_eligible`
- `Outcome Feedback Summary` should show:
  - `comparison_status`
  - `outcome_feedback_confidence`
  - `best proxy-improving arm`
  - `worst proxy-regressing arm`
  - a short delta summary for:
    - `approval_rate`
    - `default_rate_90d`
    - `avg_margin_90d`
- Detailed exporter diagnostics, full per-arm tables, and exhaustive artifact internals should stay in JSON/CSV artifacts rather than expanding the markdown review

### Claude's Discretion
- Exact JSON nesting and field grouping for telemetry and release-pack helper metadata as long as the locked canonical fields remain explicit and testable
- Exact naming for runner-local compatible evidence snapshots as long as the suite-owned milestone pack remains `release_evidence_pack.json`
- Exact markdown phrasing inside the review sections as long as the section order and required signals remain visible
- Whether a future `stale_artifact` telemetry failure reason is added later if current freshness signals are already covered by missing-artifact or ingest-lag semantics

</decisions>

<specifics>
## Specific Ideas

- The user explicitly prefers separating:
  - release-decision computation
  - telemetry operational gating
- Telemetry should gate pilot eligibility as well as broad rollout, not just production pass/fail
- The release pack should behave like a machine-readable index over canonical evidence, not a replacement for existing acceptance artifacts
- Outcome feedback should stay concise in markdown and full-fidelity in artifacts

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/ops/telemetry.py`
  - already builds exporter payloads and returns structured telemetry export results
- `credit-coach/src/credit_coach/cli/run_monitoring.py`
  - already emits `telemetry_export.json`
  - already writes `send_success_rate` and `ingest_lag_s_p95`
- `credit-coach/src/credit_coach/cli/run_production_smoke.py`
  - already consumes telemetry artifacts and enforces success-rate and ingest-lag thresholds
  - already derives `smoke_pass`, `pilot_eligible`, and `broad_rollout_allowed`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already owns canonical contract builders and markdown rendering for milestone acceptance
  - already normalizes `supporting_artifacts`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already emits seeded KPI, fairness, candidate-quality, and acceptance artifacts
  - is the natural owner for a suite-level `release_evidence_pack.json`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already emits seeded challenger summaries and supporting artifact references
  - can emit compatible local release-pack snapshots without becoming the canonical milestone pack
- `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`
  - already writes `outcome_policy_summary.csv` and `outcome_policy_deltas.json`
- `credit-coach/src/credit_coach/storage/repository.py`
  - already computes `approval_rate_delta`, `default_rate_90d_delta`, and `avg_margin_90d_delta`
- `credit-coach/tests/test_telemetry_export.py`, `credit-coach/tests/test_production_smoke.py`, `credit-coach/tests/test_phase_experiment_suite.py`, and `credit-coach/tests/test_outcome_feedback.py`
  - already give strong seams for contract-style regression coverage

### Established Patterns
- Canonical evidence lives under `artifacts/runs/<run_id>/tables/`
- JSON and CSV are the source of truth; markdown is derived
- `supporting_artifacts` is the established bridge between compact canonical decisions and deeper evidence files
- Operational decisions are already separated from pure metric aggregation in smoke and release helpers

### Integration Points
- Telemetry hardening should primarily hook into:
  - `ops/telemetry.py`
  - `cli/run_monitoring.py`
  - `cli/run_production_smoke.py`
- Release-pack standardization should primarily hook into:
  - `ops/kpi_contract.py`
  - `cli/run_phase_experiment_suite.py`
  - `cli/run_model_challenger_matrix.py`
  - `cli/run_production_smoke.py`
- Outcome-feedback linkage should primarily hook into:
  - `storage/repository.py`
  - `cli/run_outcome_feedback.py`
  - `cli/run_phase_experiment_suite.py`
- The review surface should continue to derive from canonical summaries instead of becoming a handwritten parallel path

</code_context>

<deferred>
## Deferred Ideas

- Adding richer freshness semantics such as a distinct `stale_artifact` classification can be reconsidered later if current telemetry signals prove insufficient
- A fuller operator dashboard for release evidence remains future productization work, not Phase 11
- A broader online experimentation or multi-arm outcome platform remains out of scope for this phase

</deferred>

---
*Phase: 11-release-evidence-and-outcome-feedback*
*Context gathered: 2026-03-15*
