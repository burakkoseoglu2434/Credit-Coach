# Pilot Data Contract

Bu dokuman, `run_pilot_integration` komutundan once kuruma ait export verisinin hangi minimum contract ile gelmesi gerektigini tanimlar.

Amac:

- institution-style export seam'ini tek yerde kilitlemek
- eksik veya uydurulmus mapping ile pilot run baslatmamak
- website ve operator tarafinin engine-owned contract'i tuketmesini saglamak

Bu contract live integration degildir. Validated export ingest seam'idir.

## 1. Canonical Bundle

Pilot input bir bundle dosyasi ile baslar.

Desteklenen format:

- `.json`
- `.yaml`
- `.yml`

Canonical root alanlari:

- `contract_version`
- `institution`
- `source`
- `mapping`
- `metadata`

Beklenen `contract_version`:

- `phase39.input.v1`

## 2. Institution Block

`institution` minimum olarak su alanlari tasir:

- `institution_name`
- `institution_type`

Desteklenen ama opsiyonel alanlar:

- `portfolio_focus`
- `data_readiness`
- `operator_owner`
- `notes`

Bu alanlar planning truth uretmez. Sadece operator provenance'i tasir.

## 3. Source Block

`source` minimum olarak su alanlari tasir:

- `data_path`
- `data_format`

Desteklenen `data_format`:

- `csv`
- `parquet`

Opsiyonel source metadata:

- `source_export_name`
- `exported_at`

## 4. Mapping Block

`mapping` minimum olarak su alanlari tasir:

- `customer_id_column`
- `target_column`
- `group_feature_name`
- `group_feature_column`
- `feature_columns`

Defaults:

- `group_feature_name: home_ownership`
- `feature_columns: {}`

### Mapping posture

Action / target / narrative contracts burada tekrar acilmaz.

Phase 39 mapping tavri:

- explicit mapping varsa onu kullan
- explicit mapping yoksa canonical feature adi source export'ta ayni isimle varsa identity fallback kullan
- ikisi de yoksa fail closed

## 5. Mandatory Fields

Pilot bundle ancak su alanlar valide ise ilerler:

- `customer_id_column` source data icinde var
- `target_column` source data icinde var
- `group_feature_column` source data icinde var
- tum canonical engine feature'lari ya explicit mapping ile ya identity fallback ile cozuluyor
- `customer_id` bos degil
- `customer_id` unique
- target bos degil
- group feature bos degil

Eksik veya unmappable mandatory input -> run baslamaz.

## 6. Normalized Output

Bundle valide olursa runner source export'u canonical engine kolonlarina normalize eder.

Normalized artifact:

- `tables/pilot_normalized_input.parquet`

Bu artifact su alanlari tasir:

- `customer_id`
- tum canonical engine features
- canonical target column
- canonical group feature column

Bu artifact yeni planner yaratmaz; mevcut batch planning core'a handoff edilir.

## 7. Input Manifest

Runner normalize ettikten sonra:

- `tables/pilot_input_manifest.json`

uretmelidir.

Bu manifest su truth'leri tasir:

- source export path
- normalized row count
- group feature name
- explicit feature count
- identity fallback feature list
- canonical feature -> source column provenance

## 8. Minimal Example

```json
{
  "contract_version": "phase39.input.v1",
  "institution": {
    "institution_name": "Example Bank",
    "institution_type": "bank",
    "portfolio_focus": "denied recovery"
  },
  "source": {
    "data_path": "pilot/source_export.csv",
    "data_format": "csv",
    "source_export_name": "march_export"
  },
  "mapping": {
    "customer_id_column": "customer_key",
    "target_column": "outcome_label",
    "group_feature_name": "home_ownership",
    "group_feature_column": "home_owner_group",
    "feature_columns": {
      "annual_inc": "documented_income_amount"
    }
  }
}
```

## 9. Emitted Package Overview

Basarili bir pilot run sonunda operator en az su engine-owned artifact'leri beklemelidir:

- `pilot_input_manifest.json`
- `pilot_package_manifest.json`
- `batch_summary.json`
- `portfolio_validation_summary.json`
- `product_confidence_snapshot.json`
- `pilot_guardrails.json`
- `milestone_acceptance_summary.json`

Sonraki adimlar:

- [PILOT_EXECUTION_GUIDE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_EXECUTION_GUIDE.md)
- [PILOT_PACKAGE_SCHEMA.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_PACKAGE_SCHEMA.md)
