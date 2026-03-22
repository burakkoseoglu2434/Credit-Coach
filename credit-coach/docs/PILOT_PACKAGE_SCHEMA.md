# Pilot Package Schema

Bu dokuman `run_pilot_integration` tarafindan emitted edilen pilot package'in contract'ini tanimlar.

Canonical manifest:

- `tables/pilot_package_manifest.json`

## 1. Package Truth

Pilot package bir website snapshot'i degil.
Engine-owned release and validation package'idir.

Manifest minimum olarak su alanlari tasir:

- `contract_version`
- `run_id`
- `generated_at`
- `institution`
- `input_contract_version`
- `source_data_path`
- `normalized_input_path`
- `normalized_row_count`
- `group_feature_name`
- `batch_run_id`
- `batch_artifact_dir`
- `release_decision`
- `acceptance_status`
- `pilot_eligible`
- `broad_rollout_allowed`
- `required_artifacts`
- `optional_artifacts`
- `mapping_provenance`

Beklenen package contract version:

- `phase39.package.v1`

## 2. Required Artifacts

Phase 39 pilot package minimum olarak su artifact referanslarini tasir:

- `pilot_input_manifest_json`
- `batch_summary_json`
- `portfolio_validation_summary_json`
- `portfolio_validation_review_md`
- `product_confidence_snapshot_json`
- `pilot_guardrails_json`
- `kpi_contract_snapshot_json`
- `milestone_acceptance_summary_json`
- `release_evidence_pack_json`

## 3. Optional Artifacts

Opsiyonel ama beklenen destek artifact'leri:

- `portfolio_numeric_impact_breakdown_csv`
- `portfolio_segment_breakdown_csv`
- `portfolio_offer_diagnostics_csv`
- `demo_representativeness_summary_json`
- `portfolio_calibration_validation_breakdown_csv`
- `rollback_conditions_json`
- `pilot_calibration_summary_json`

## 4. Guardrail Fields

Pilot package icinde `pilot_guardrails.json` su truth'leri tasir:

- `pilot_eligible`
- `broad_rollout_allowed`
- `max_traffic_pct`
- `fairness_monitoring_required`
- `rollback_guard_required`
- `targeted_alerting_required`
- `manual_approval_required`
- `remediation_artifacts_required`
- `dominant_fail_segment_key`
- `dominant_fail_candidate_source`

## 5. Acceptance Fields

Acceptance posture iki yerde gorunur:

- `milestone_acceptance_summary.json`
- `release_evidence_pack.json`

Phase 39 icin en onemli alanlar:

- `release_decision`
- `acceptance_status`
- `acceptance_eligible`
- `evidence_level`
- `evidence_status`
- `degraded_reason`

Beklenen okuma:

- `acceptance_status = PILOT_ONLY`
  - controlled pilot icin savunulabilir
  - broad rollout karari degil

## 6. Provenance

Pilot package provenance su zinciri korur:

1. raw institution export
2. validated bundle
3. normalized pilot parquet
4. existing batch planning core
5. mirrored portfolio artifacts
6. pilot-specific manifest and guardrails

Package, website tarafinda yeni anlam uretilmeden tuketilmelidir.

## 7. Website Handoff

Website pilot handoff icin ana referanslar:

- [PILOT_READINESS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/PILOT_READINESS.md)
- [CURATED_DEMO_HANDOFF.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/CURATED_DEMO_HANDOFF.md)

Bu docs artik `pilot package` ve `product_confidence_snapshot` diliyle konusmalidir; parallel website-only pilot story olusturulmamali.
