# Phase 9: KPI Contract Unification - Context

**Gathered:** 2026-03-14
**Status:** Ready for execution

<domain>
## Phase Boundary

Align the existing KPI contract across smoke, phase-suite, and challenger workflows; freeze model state explicitly for repeated seeded comparisons; and define milestone acceptance from repeated seeded evidence. This phase hardens how release and milestone evidence is represented and consumed; it does not add new end-user capabilities or new KPI families.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phase 8
- Phase 8 release semantics remain authoritative and are not reopened in this phase:
  - `reliability_pass == false` -> `NO_GO`
  - `lift_pass == false` -> `NO_GO`
  - otherwise evaluate fairness-driven `GO | LIMITED_GO | NO_GO`
- Phase 9 must preserve the Phase 8 evidence principle:
  - machine-readable artifacts are the canonical source of truth
  - human-readable summaries are derived companions only

### Canonical KPI Artifact
- Phase 9 must introduce one canonical KPI contract artifact shared conceptually across suite, smoke, and challenger flows
- Canonical artifact name:
  - `kpi_contract_snapshot.json`
- Artifact role:
  - runner-level source of truth for KPI contract status and release semantics
- Format policy:
  - JSON is the canonical decision and state artifact
  - CSV files remain companion evidence for seed, row, and breakdown detail
- Scope of the canonical artifact:
  - aggregate KPI decision state
  - release semantics
  - fairness localization summary
  - evidence completeness
  - frozen snapshot metadata
- The canonical artifact should reference detailed evidence rather than embedding all seed rows directly
  - e.g. `phase_scale_seed_summary.csv`
  - e.g. `fairness_failure_breakdown.csv`
  - e.g. challenger variant summary tables
- Every runner should compute its own KPI state from its own evidence, but emit the same canonical schema
- Runner-specific artifacts may remain, but they are secondary or local evidence rather than the source of truth

### Frozen Snapshot Handoff
- Explicit freeze selectors must support:
  - `--model_version`
  - `--model_manifest`
- CLI inputs are not the source of truth by themselves; all selectors must be resolved into one canonical resolved manifest object before downstream execution
- If both `--model_version` and `--model_manifest` are provided:
  - the system may accept both
  - but version consistency must be checked
  - mismatch is a hard failure
- Train-once suite execution must write a dedicated frozen snapshot artifact:
  - `frozen_model_manifest.json`
- `kpi_contract_snapshot.json` should reference that frozen snapshot artifact rather than duplicating all freeze metadata inline
- `frozen_model_manifest.json` should include at minimum:
  - `model_version`
  - `training_run_id`
  - `manifest_path`
  - `config_hash`
  - `feature_schema_hash`
  - `artifact_hash` or equivalent integrity field
  - `resolved_at`
  - `resolved_by_runner`
- Explicit freeze mode must fail closed:
  - if an explicit selector cannot be resolved, read, or validated, execution fails
  - no implicit fallback to `latest.json` is allowed in explicit freeze mode
- Legacy or dev convenience mode may still allow implicit `latest.json` resolution only when no explicit selector is provided
- When implicit latest-mode is used:
  - `freeze_mode = implicit_latest`
  - `acceptance_eligible = false`
- Challenger freeze scope is variant-level:
  - each variant is trained or resolved once
  - one frozen bundle is produced per variant
  - all seed runs for that variant reuse the same frozen bundle
- If a challenger variant is pre-trained rather than freshly trained, it must still resolve to the same frozen-manifest contract before downstream seeded runs execute

### Degraded Evidence Policy
- Repeated seeded evidence is the standard acceptance-grade evidence for Phase 9
- If repeated seeded evidence is missing, the system may still compute a `release_decision`
- Degraded single-run decisions must be marked explicitly:
  - `evidence_level = single_run_fallback`
  - preferred companion field: `evidence_status = degraded`
- If repeated seeded evidence is missing:
  - `acceptance_eligible = false`
- Degraded evidence can produce an operational signal, but it cannot close milestone acceptance and cannot satisfy `KPI-03`
- Single-run fallback must never authorize broad production by itself
- In degraded evidence mode:
  - `release_decision` may still be `GO | LIMITED_GO | NO_GO`
  - `broad_rollout_allowed = false`
  - the result is operational only, not acceptance-grade
- Even in degraded mode, the runner must still emit:
  - `kpi_contract_snapshot.json`
- Degraded `kpi_contract_snapshot.json` must include at minimum:
  - `evidence_level`
  - `acceptance_eligible`
  - `degraded_reason`
  - `missing_artifacts`
- Strongly preferred additional degraded fields:
  - `release_decision`
  - `smoke_pass`
  - `pilot_eligible`
  - `broad_rollout_allowed`
  - `fallback_source`

### Acceptance Bundle Shape
- Milestone-level canonical acceptance artifact name:
  - `milestone_acceptance_summary.json`
- This artifact is distinct from the runner-level contract artifact:
  - `kpi_contract_snapshot.json` is runner-level
  - `milestone_acceptance_summary.json` is milestone-level
- Acceptance statuses are fixed to:
  - `ACCEPTED`
  - `PILOT_ONLY`
  - `REJECTED`
- Status mapping should follow the locked release semantics:
  - `GO -> ACCEPTED`
  - `LIMITED_GO -> PILOT_ONLY`
  - `NO_GO -> REJECTED`
- Degraded evidence should not introduce a fourth acceptance status
- Degraded behavior should instead be represented through:
  - `acceptance_eligible`
  - `evidence_level`
  - `degraded_reason`
- `milestone_acceptance_summary.json` must include at minimum:
  - `phase`
  - `milestone`
  - `contract_version`
  - `runner_type`
  - `evidence_level`
  - `acceptance_eligible`
  - `acceptance_status`
  - `release_decision`
  - `broad_rollout_allowed`
  - `model_freeze_mode`
  - `model_version`
  - `seed_count`
  - `fairness_seed_pass_count`
  - `lift_pass`
  - `reliability_pass`
  - `primary_fairness_metric`
  - `worst_primary_fairness_gap`
  - `dominant_fail_segment_key`
  - `dominant_fail_candidate_source`
  - `supporting_artifacts`
  - `generated_at`
- The following fields are conditionally mandatory in degraded evidence mode:
  - `degraded_reason`
  - `missing_artifacts`
- Human-readable milestone review companion:
  - `milestone_acceptance_review.md`
- The review markdown must be derived only from `milestone_acceptance_summary.json`
- Suggested review sections:
  - Decision
  - Reason summary
  - Freeze / provenance
  - Dominant failure localization
  - Supporting artifacts

### Claude's Discretion
- Exact JSON nesting is flexible as long as the locked field names remain explicit and testable
- Integrity field naming may vary (`artifact_hash`, `manifest_hash`, etc.) as long as one clear bundle-integrity signal exists
- Runner-specific companion artifact names may remain if they map cleanly into `supporting_artifacts`
- Whether degraded helper metadata uses one field or a small structured block is flexible if the locked degraded fields remain explicit

</decisions>

<specifics>
## Specific Ideas

- `kpi_contract_snapshot.json` should become the contract-shaped runner output that smoke, suite, and challenger all emit
- `frozen_model_manifest.json` should be the canonical freeze artifact reused by seeded suite and challenger runs
- `milestone_acceptance_summary.json` should stay lightweight and decision-focused rather than turning into a full Phase 11 release pack
- Smoke may continue to produce local gate and monitoring artifacts, but those should map back to the canonical KPI contract output

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already defines canonical threshold keys and default threshold values
  - is the natural home for shared KPI comparator and snapshot helpers
- `credit-coach/src/credit_coach/ops/release_decision.py`
  - already owns the Phase 8 release semantics
  - should remain layered above the unified KPI contract rather than being reimplemented elsewhere
- `credit-coach/src/credit_coach/model/registry.py`
  - already writes versioned manifests and `latest.json`
  - is the natural place to add explicit bundle resolution by model version or manifest path
- `credit-coach/src/credit_coach/cli/run_train.py`
  - already produces `model_version` and manifest outputs that can feed the frozen-model contract
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already writes `batch_run_manifest.json`
  - currently loads the latest model bundle implicitly
- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - also loads the latest model bundle implicitly
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already captures `train_run_id`
  - already writes seeded suite artifacts and release summaries
  - is the natural anchor for repeated-evidence acceptance
- `credit-coach/src/credit_coach/cli/run_production_smoke.py`
  - already writes `kpi_snapshot.json`
  - already supports optional `phase_scale_aggregate.json` consumption
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already calculates variant-scoped evidence and promotion signals
  - should emit the canonical KPI schema while keeping runner-local calculations independent

### Established Patterns
- Artifact-first execution under `artifacts/runs/<run_id>/tables/`
- Config-first contract behavior using YAML-backed thresholds
- JSON for canonical machine-readable decisions, CSV for tabular evidence
- Flat pytest contract tests around runner seams

### Integration Points
- Phase 9 changes must hook into:
  - `run_phase_experiment_suite.py`
  - `run_production_smoke.py`
  - `run_model_challenger_matrix.py`
  - `run_batch_recourse_eval.py`
  - `run_recourse.py`
  - `model/registry.py`
- Execution should ensure runner-local artifacts remain traceable through:
  - `kpi_contract_snapshot.json`
  - `frozen_model_manifest.json`
  - `milestone_acceptance_summary.json`

</code_context>

<deferred>
## Deferred Ideas

None - discussion stayed inside the Phase 9 boundary

</deferred>

---
*Phase: 09-kpi-contract-unification*
*Context gathered: 2026-03-14*
