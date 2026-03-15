# Phase 11: Release Evidence and Outcome Feedback - Research

**Researched:** 2026-03-15
**Status:** Ready for replanning
**Confidence:** HIGH

## Planning Question

What has to change so production-like release evidence becomes fail-closed, reproducible, and connected to business-impact proxies without weakening the seeded fairness and KPI contracts from Phases 8-10?

## Planning Assumption

This research pass is the forced re-research step after `11-CONTEXT.md` captured the user decisions that planning had previously lacked. The authoritative inputs for this pass are:

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/11-release-evidence-and-outcome-feedback/11-CONTEXT.md`
- Phase 8, Phase 9, and Phase 10 outputs
- current CLI and test code under `credit-coach/src/credit_coach/` and `credit-coach/tests/`

That is sufficient because `OPS-01`, `OPS-02`, and `OPS-03` are concrete, the user has now locked the remaining operational interpretation choices, and the repo already contains telemetry export, release-decision, and outcome-feedback primitives. The remaining work is contract hardening plus artifact unification, not open-ended product discovery.

## Executive Summary

Phase 11 should not invent a new governance model. The repo already exports telemetry, already evaluates production smoke gates, already emits seeded acceptance artifacts, and already stores delayed outcome feedback. What remains is to force those capabilities into one release-ready operational contract shaped by the newly locked context.

This makes Phase 11 a hardening and packaging phase. The main job is to keep `release_decision` computation separate from telemetry gating, fail closed operationally when telemetry evidence is missing or unhealthy, publish one suite-owned stable release evidence bundle that points to fairness, trajectory, telemetry, and seed-summary artifacts, and connect offline KPI movement to business-impact proxy reports without diluting the shared seeded acceptance logic from Phase 9.

The recommended execution order remains:

- enforce telemetry-required production profile and exporter-health semantics
- standardize reproducible release evidence packs and milestone decision bundles
- publish outcome-feedback and policy-delta reports as companion evidence for release review

## Existing Assets We Can Reuse

### Telemetry export and health metrics already exist

- `credit-coach/src/credit_coach/ops/telemetry.py`
  - already builds structured telemetry metrics from monitoring summary inputs
  - already supports exporter modes and structured export results
- `credit-coach/src/credit_coach/cli/run_monitoring.py`
  - already writes `telemetry_export.json`
  - already enriches telemetry payloads with `send_success_rate`
  - already enriches telemetry payloads with `ingest_lag_s_p95`
- `credit-coach/tests/test_telemetry_export.py`
  - already covers the exporter layer directly

This means `OPS-01` is not about inventing telemetry. It is about turning telemetry health into a production-profile requirement that broad rollout and pilot operation cannot bypass.

### Production smoke already understands telemetry and seeded acceptance artifacts

- `credit-coach/src/credit_coach/cli/run_production_smoke.py`
  - already consumes `telemetry_json`
  - already exposes `--require_telemetry_enabled`
  - already exposes `--min_telemetry_success_rate`
  - already exposes `--max_telemetry_ingest_lag_s`
  - already consumes `phase_scale_aggregate.json`
  - already consumes `milestone_acceptance_summary.json`
- `credit-coach/tests/test_production_smoke.py`
  - already protects smoke gating behavior and release-decision semantics

This means the enforcement seam for `OPS-01` already exists. Phase 11 should tighten telemetry failure classification, pilot/broad-rollout semantics, and artifact traceability around it.

### Seeded acceptance and milestone summaries already exist

- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already defines canonical runner-level and milestone-level contract builders
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already emits `kpi_contract_snapshot.json`
  - already emits `milestone_acceptance_summary.json`
  - already emits seeded suite artifacts such as `phase_scale_seed_summary.csv`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already emits comparable seeded variant outputs for challenger analysis

This means `OPS-02` should extend the existing contract with a suite-owned stable release-pack layer rather than create a second acceptance lane.

### Outcome feedback already exists, but lives outside the release-review path

- `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`
  - already ingests delayed outcomes
  - already writes `outcome_policy_summary.csv`
  - already writes `outcome_policy_deltas.json`
- `credit-coach/src/credit_coach/storage/repository.py`
  - already computes policy-arm deltas for approval rate, default rate, and margin
- `credit-coach/tests/test_outcome_feedback.py`
  - already covers the current reporting workflow

This means `OPS-03` is an integration and interpretation gap, not a greenfield analytics problem. The main open question was comparison policy, and that is now locked.

## Gaps Phase 11 Must Close

### 1. Telemetry can be present without being a fail-closed production prerequisite

The repo can already export telemetry and smoke can already read it, but Phase 11 still needs a deterministic production-profile contract that makes missing, disabled, failed, low-success-rate, or high-ingest-lag telemetry block both broad rollout and pilot eligibility without rewriting the underlying `release_decision`.

### 2. Release evidence exists, but not yet as one stable bundle

Fairness, trajectory, seeded acceptance, and telemetry artifacts already exist across multiple runners, but Phase 11 still needs one suite-owned reproducible bundle that points to them from stable `tables/`-relative locations, always writes explicit completeness metadata, and keeps milestone review deterministic.

### 3. Outcome feedback exists, but not yet as release evidence

Outcome deltas currently live in their own reporting lane. Phase 11 needs to surface them as companion evidence that helps explain whether offline KPI movement aligns with business-impact proxies such as approval rate, 90-day default behavior, and observed margin under a default `treatment vs control` interpretation.

### 4. Phase 11 must not reopen the acceptance contract

Phases 8-10 already locked seeded fairness, KPI, candidate-quality, and impact-review semantics. Phase 11 should attach telemetry and outcome evidence to those contracts, not replace them or invent a new gating hierarchy, new release precedence, or new review style.

## Context-Locked Operational Interpretation

### Telemetry health should behave like an operational gate, not a second release-decision engine

The target state for `OPS-01` is:

- `release_decision` is still computed from the existing KPI and fairness contract
- telemetry is applied as a separate operational gate
- degraded telemetry blocks `broad_rollout_allowed`
- degraded telemetry also blocks `pilot_eligible`
- telemetry failures are classified explicitly, not inferred from logs

The locked canonical failure reasons are:

- `missing_artifact`
- `disabled_exporter`
- `export_failed`
- `success_rate_below_threshold`
- `ingest_lag_above_threshold`

### Release evidence bundles should be canonical, reproducible, and source-of-truth friendly

The target state for `OPS-02` is a suite-owned `release_evidence_pack.json` that points to:

- fairness artifacts
- trajectory artifacts
- telemetry artifacts
- seed-summary artifacts
- milestone acceptance artifacts
- candidate-quality artifacts

The pack must:

- use `tables/`-relative paths
- always be written, even when degraded
- expose `pack_status = complete | degraded`
- expose `missing_artifacts`, `required_artifacts`, `optional_artifacts`, and `pack_acceptance_eligible`

The canonical truth remains machine-readable. Markdown review remains derived.

### Outcome feedback should stay comparative and proxy-oriented

The target state for `OPS-03` is not a full online experimentation platform. It is a release-review companion that connects offline KPI movement to business-impact proxies through:

- outcome policy summaries
- policy-arm deltas
- explicit references to approval, default, and margin movement
- default `treatment vs control` language
- descriptive fallback when control is missing

That keeps the phase honest and aligned with current repo capabilities.

### Review should remain explanation-first

The review surface is now locked to this default order:

- `Decision`
- `Telemetry Readiness`
- `Release Pack Completeness`
- `Outcome Feedback Summary`
- `Supporting Artifacts`

It should open with an explicit evidence-status line such as `complete` or `degraded` plus the primary reason.

## Recommended Architecture

### A. Treat telemetry health as a first-class operational gate input

Use `run_monitoring.py` and `run_production_smoke.py` as the authoritative path. Monitoring should emit structured exporter-health evidence, and smoke should fail closed operationally whenever telemetry evidence is missing, disabled, failed, or degraded beyond configured thresholds. The telemetry gate should modify rollout eligibility, not overwrite the shared `release_decision`.

### B. Standardize one suite-owned release-pack manifest instead of scattering path logic

Extend suite outputs so milestone review can rely on one stable `release_evidence_pack.json` that references fairness, trajectory, telemetry, seeded KPI contract, candidate-quality, and acceptance outputs. Smoke and challenger may emit compatible local snapshots, but the milestone-level source of truth remains the suite pack. This should complement `kpi_contract_snapshot.json` and `milestone_acceptance_summary.json`, not replace them.

### C. Keep outcome feedback machine-readable and release-review aligned

Outcome feedback should continue to emit raw tables and deltas, then add a machine-readable summary artifact that can be linked from release evidence packs and milestone review. Machine-readable outputs should support all arms relative to control when available, while the human-readable review should summarize only the best proxy-improving arm and worst proxy-regressing arm.

### D. Preserve the seeded acceptance stack from earlier phases

Phase 11 should be additive. Release packs and outcome reports should point to Phase 8-10 artifacts and enrich them with operational evidence, not redefine the underlying fairness or KPI contracts.

## Artifact Contract Recommended For Phase 11

### Canonical operational artifacts

- `telemetry_export.json`
- `kpi_contract_snapshot.json`
- `milestone_acceptance_summary.json`
- `release_evidence_pack.json`
- `release_decision.json`
- `outcome_policy_summary.csv`
- `outcome_policy_deltas.json`
- `outcome_feedback_summary.json`

### Derived human-readable artifact

- `release_review_summary.md`

The canonical source of truth should remain JSON and CSV. The markdown review should stay concise, derived from those artifacts, and front-load evidence completeness plus telemetry readiness.

## Recommended Plan Breakdown

### Plan 11-01: Telemetry-required production profile

Focus on exporter-health semantics, fail-closed telemetry requirements, and production-smoke enforcement for `OPS-01`.

### Plan 11-02: Reproducible release evidence packs

Focus on stable pack layout, machine-readable bundle references, and milestone decision packaging for `OPS-02`.

### Plan 11-03: Outcome feedback and policy-delta linkage

Focus on linking outcome reports to business-impact proxies and release evidence for `OPS-03`.

## Risks To Avoid

- treating telemetry as optional metadata in production-profile mode
- letting degraded telemetry preserve pilot eligibility
- duplicating acceptance logic outside the Phase 9 contract
- turning smoke or challenger local evidence snapshots into milestone-level source of truth
- over-claiming policy impact when the control baseline is missing
- mixing human-readable summaries into canonical evidence
- expanding Phase 11 into a full dashboard or experimentation platform

## Recommendation

Proceed with execution planning for Phase 11 as a hardening phase:

1. make telemetry health fail closed for production-profile semantics
2. publish stable release evidence packs that unify seeded, fairness, trajectory, and telemetry artifacts
3. connect outcome-feedback and policy-delta reporting into release review as machine-readable companion evidence
