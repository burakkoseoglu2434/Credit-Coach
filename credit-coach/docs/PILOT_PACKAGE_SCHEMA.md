# Pilot Package Schema

Bu dokuman Phase 44 sonrasi iki ana contract'i tanimlar:

- `pilot_package_manifest.json`
- `pilot_refresh_manifest.json`

Ayrica institution-facing explanation-pack referansini da kapsar.

## 1. Contract Versions

Canonical version'lar:

- pilot input: `phase39.input.v1`
- pilot package: `phase39.package.v1`
- pilot refresh: `phase44.refresh.v1`
- decision explanation pack: `phase44.explanation.v1`

## 2. Pilot Package Manifest

Canonical path:

- `tables/pilot_package_manifest.json`

Minimum alanlar:

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

Phase 44 additive alanlar:

- `overlay_provenance`
- `refresh_provenance`
- `resolved_runtime_config`
- `institution_profile_key`
- `policy_version_evaluated`
- `explanation_artifacts`

Kural:

- eski package okumalari kirilmaz
- yeni Phase 44 alanlari additive kalir

## 3. Pilot Refresh Manifest

Canonical path:

- `tables/pilot_refresh_manifest.json`

Minimum alanlar:

- `contract_version`
- `run_id`
- `generated_at`
- `cadence_mode`
- `institution_profile_key`
- `selection_policy_name`
- `selection_fill_behavior`
- `policy_version_evaluated`
- `collection_run_id`
- `collection_manifest_path`
- `pilot_package_run_id`
- `pilot_package_manifest_path`
- `smoke_run_id`
- `smoke_summary_path`
- `artifact_qa_status`
- `portfolio_smoke_status`
- `reference_run_id`
- `reference_label`
- `comparison_is_canonical`
- `refresh_context`
- `resolved_runtime_config`
- `overlay_provenance`
- `comparison_summary`
- `output_artifacts`

Bu manifest refresh cadence, comparison ve dual-lane gate'leri tek yerde toplar.

## 4. Required Output Artifacts

Phase 44 refresh altinda minimum beklenen artifact'ler:

- `pilot_refresh_summary.md`
- `policy_version_comparison.csv`
- `policy_version_comparison.md`
- `artifact_qa_summary.json`
- `release_smoke_summary.json`
- `refresh_context.json`

## 5. Explanation Artifacts

Pilot package ve refresh manifest su referansi tasiyabilir:

- `decision_explanation_packs_root`

Bu root altinda her musteri icin:

- `decision_explanation_pack.json`
- `decision_explanation_pack.md`

uretilir.

## 6. QA Vocabulary

Artifact QA yalnizca su vocabulary'yi kullanir:

- `PASS`
- `DEGRADED`
- `FAIL`

Kural:

- `portfolio_smoke_status` ile karistirilmaz
- refresh summary'de ayri okunur

## 7. Provenance Rules

Thin overlay provenance gorunur olmalidir:

- `institution_policy`
- `institution_offer`
- `pilot_profile`

Resolve edilmis runtime config da ayrica yazilmalidir.

Bu Phase 44'te live config sync anlamina gelmez.
Sadece local, reproducible overlay provenance anlamina gelir.

## 8. Non-Leakage Rule

Institution-facing package referanslari su internal truth'leri disari tasimaz:

- `NEEDS_REVIEW`
- raw gate trace
- debug-only QA detail dump
- candidate policy tables

Proof without leakage ana kuraldir.

## 9. Related Docs

- [PILOT_EXECUTION_GUIDE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_EXECUTION_GUIDE.md)
- [DECISION_EXPLANATION_PACK.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/DECISION_EXPLANATION_PACK.md)
- [PILOT_READINESS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/PILOT_READINESS.md)
