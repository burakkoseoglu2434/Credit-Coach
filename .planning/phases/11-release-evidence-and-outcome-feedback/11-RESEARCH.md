# Phase 11: Release Evidence and Outcome Feedback - Research

**Researched:** 2026-03-15
**Status:** Ready for execution planning
**Confidence:** HIGH

## Planning Question

What has to change so production-like release evidence becomes fail-closed, reproducible, and connected to business-impact proxies without weakening the seeded fairness and KPI contracts from Phases 8-10?

## Planning Assumption

This planning pass proceeds without `11-CONTEXT.md`. The authoritative inputs for this phase are:

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- Phase 8, Phase 9, and Phase 10 outputs
- current CLI and test code under `credit-coach/src/credit_coach/` and `credit-coach/tests/`

That is sufficient because `OPS-01`, `OPS-02`, and `OPS-03` are concrete, the repo already contains telemetry export, release-decision, and outcome-feedback primitives, and the remaining work is mainly contract hardening plus artifact unification.

## Executive Summary

Phase 11 should not invent a new governance model. The repo already exports telemetry, already evaluates production smoke gates, already emits seeded acceptance artifacts, and already stores delayed outcome feedback. What remains is to force those capabilities into one release-ready operational contract.

This makes Phase 11 a hardening and packaging phase. The main job is to fail closed when telemetry evidence is missing or unhealthy, publish stable release evidence bundles that point to fairness, trajectory, telemetry, and seed-summary artifacts, and connect offline KPI movement to business-impact proxy reports without diluting the shared seeded acceptance logic from Phase 9.

The recommended execution order is:

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

This means `OPS-01` is not about inventing telemetry. It is about turning telemetry health into a production-profile requirement that broad rollout cannot bypass.

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

This means the enforcement seam for `OPS-01` already exists. Phase 11 should tighten defaults, degraded-evidence semantics, and artifact traceability around it.

### Seeded acceptance and milestone summaries already exist

- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already defines canonical runner-level and milestone-level contract builders
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already emits `kpi_contract_snapshot.json`
  - already emits `milestone_acceptance_summary.json`
  - already emits seeded suite artifacts such as `phase_scale_seed_summary.csv`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already emits comparable seeded variant outputs for challenger analysis

This means `OPS-02` should extend the existing contract with stable release-pack locations rather than create a second acceptance lane.

### Outcome feedback already exists, but lives outside the release-review path

- `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`
  - already ingests delayed outcomes
  - already writes `outcome_policy_summary.csv`
  - already writes `outcome_policy_deltas.json`
- `credit-coach/src/credit_coach/storage/repository.py`
  - already computes policy-arm deltas for approval rate, default rate, and margin
- `credit-coach/tests/test_outcome_feedback.py`
  - already covers the current reporting workflow

This means `OPS-03` is an integration and interpretation gap, not a greenfield analytics problem.

## Gaps Phase 11 Must Close

### 1. Telemetry can be present without being a fail-closed production prerequisite

The repo can already export telemetry and smoke can already read it, but Phase 11 still needs a deterministic production-profile contract that makes missing, disabled, stale, or unhealthy telemetry broad-rollout blocking rather than optional metadata.

### 2. Release evidence exists, but not yet as one stable bundle

Fairness, trajectory, seeded acceptance, and telemetry artifacts already exist across multiple runners, but Phase 11 still needs a reproducible bundle or manifest that points to them from stable locations and keeps milestone review deterministic.

### 3. Outcome feedback exists, but not yet as release evidence

Outcome deltas currently live in their own reporting lane. Phase 11 needs to surface them as companion evidence that helps explain whether offline KPI movement aligns with business-impact proxies such as approval rate, 90-day default behavior, and observed margin.

### 4. Phase 11 must not reopen the acceptance contract

Phases 8-10 already locked seeded fairness, KPI, candidate-quality, and impact-review semantics. Phase 11 should attach telemetry and outcome evidence to those contracts, not replace them or invent a new gating hierarchy.

## Context-Locked Operational Interpretation

### Telemetry health should behave like production evidence, not best-effort logging

The target state for `OPS-01` is a production profile that fails closed when telemetry export is disabled or degraded. That means:

- missing telemetry artifacts must be visible as degraded evidence
- unhealthy export status must block broad rollout
- success-rate and ingest-lag metrics must remain machine-readable and deterministic

### Release evidence bundles should be canonical, reproducible, and source-of-truth friendly

The target state for `OPS-02` is a stable evidence-pack layer that points to:

- fairness artifacts
- trajectory artifacts
- telemetry artifacts
- seed-summary artifacts
- milestone acceptance artifacts

The canonical truth should remain machine-readable. Markdown review remains derived.

### Outcome feedback should stay comparative and proxy-oriented

The target state for `OPS-03` is not a full online experimentation platform. It is a release-review companion that connects offline KPI movement to business-impact proxies through:

- outcome policy summaries
- policy-arm deltas
- explicit references to approval, default, and margin movement

That keeps the phase honest and aligned with current repo capabilities.

## Recommended Architecture

### A. Treat telemetry health as a first-class production gate input

Use `run_monitoring.py` and `run_production_smoke.py` as the authoritative path. Monitoring should emit structured exporter-health evidence, and smoke should fail closed for production-profile semantics whenever telemetry evidence is missing, disabled, unhealthy, or degraded beyond configured thresholds.

### B. Standardize one release-pack manifest instead of scattering path logic

Extend suite and challenger outputs so milestone review can rely on one stable evidence manifest or pack summary that references fairness, trajectory, telemetry, seeded KPI contract, and acceptance outputs. This should complement `kpi_contract_snapshot.json` and `milestone_acceptance_summary.json`, not replace them.

### C. Keep outcome feedback machine-readable and release-review aligned

Outcome feedback should continue to emit raw tables and deltas, then add a machine-readable summary artifact that can be linked from release evidence packs and milestone review. Human-readable release review should derive from these machine-readable sources.

### D. Preserve the seeded acceptance stack from earlier phases

Phase 11 should be additive. Release packs and outcome reports should point to Phase 8-10 artifacts and enrich them with operational evidence, not redefine the underlying fairness or KPI contracts.

## Artifact Contract Recommended For Phase 11

### Canonical operational artifacts

- `telemetry_export.json`
- `kpi_contract_snapshot.json`
- `milestone_acceptance_summary.json`
- `release_evidence_pack.json`
- `outcome_policy_summary.csv`
- `outcome_policy_deltas.json`
- `outcome_feedback_summary.json`

### Derived human-readable artifact

- `release_review_summary.md`

The canonical source of truth should remain JSON and CSV. The markdown review should stay concise and derived from those artifacts.

## Recommended Plan Breakdown

### Plan 11-01: Telemetry-required production profile

Focus on exporter-health semantics, fail-closed telemetry requirements, and production-smoke enforcement for `OPS-01`.

### Plan 11-02: Reproducible release evidence packs

Focus on stable pack layout, machine-readable bundle references, and milestone decision packaging for `OPS-02`.

### Plan 11-03: Outcome feedback and policy-delta linkage

Focus on linking outcome reports to business-impact proxies and release evidence for `OPS-03`.

## Risks To Avoid

- treating telemetry as optional metadata in production-profile mode
- duplicating acceptance logic outside the Phase 9 contract
- mixing human-readable summaries into canonical evidence
- expanding Phase 11 into a full dashboard or experimentation platform

## Recommendation

Proceed with execution planning for Phase 11 as a hardening phase:

1. make telemetry health fail closed for production-profile semantics
2. publish stable release evidence packs that unify seeded, fairness, trajectory, and telemetry artifacts
3. connect outcome-feedback and policy-delta reporting into release review as machine-readable companion evidence
