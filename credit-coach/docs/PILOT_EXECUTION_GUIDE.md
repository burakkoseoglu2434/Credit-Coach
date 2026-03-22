# Pilot Execution Guide

Bu runbook, operator'un validated pilot bundle'i alip engine-owned pilot package'e cevirmesi icindir.

Bu guide live bank integration anlatmaz.
Bu guide controlled pilot package execution anlatir.

## 1. Input

Pilot run icin once bundle hazir olmalidir.

Bkz:

- [PILOT_DATA_CONTRACT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_DATA_CONTRACT.md)

Minimum giris:

- institution context
- source export path
- target column
- group feature column
- feature mapping overrides gerekiyorsa onlar

## 2. Command

Canonical komut:

```bash
cd credit-coach
python -m credit_coach.cli.run_pilot_integration \
  --pilot_bundle /absolute/path/to/pilot_bundle.json
```

Ihtiyaca gore su config override'lari verilebilir:

- `--base_config`
- `--model_config`
- `--recourse_config`
- `--causality_config`
- `--safety_config`
- `--macro_config`
- `--kpi_contract`
- `--group_feature`
- `--n_customers`
- `--sample_seed`

## 3. Runtime Flow

Runner su sirayla calisir:

1. bundle contract validate edilir
2. institution export okunur
3. data canonical engine kolonlarina normalize edilir
4. `pilot_input_manifest.json` yazilir
5. mevcut `run_batch_recourse_eval` planning core'u calistirilir
6. batch artifact'leri pilot package altina mirror edilir
7. `product_confidence_snapshot`, `pilot_guardrails`, `kpi_contract_snapshot`, `milestone_acceptance_summary` ve `pilot_package_manifest` uretilir

Kural:

- engine produces
- website and operators consume

## 4. Core Output Package

Pilot package altinda beklenen ana artifact'ler:

- `pilot_package_manifest.json`
- `pilot_input_manifest.json`
- `batch_summary.json`
- `portfolio_validation_summary.json`
- `portfolio_validation_review.md`
- `portfolio_calibration_validation_breakdown.csv`
- `product_confidence_snapshot.json`
- `pilot_guardrails.json`
- `rollback_conditions.json`
- `kpi_contract_snapshot.json`
- `milestone_acceptance_summary.json`
- `release_evidence_pack.json`

## 5. How To Read The Package

### First read

1. `pilot_package_manifest.json`
2. `milestone_acceptance_summary.json`
3. `pilot_guardrails.json`
4. `product_confidence_snapshot.json`
5. `portfolio_validation_summary.json`

### Why this order

- manifest -> provenance
- acceptance summary -> overall posture
- guardrails -> what must stay controlled
- product confidence -> buyer-safe truth
- portfolio validation -> deeper engine truth

## 6. Acceptance Posture

Phase 39 pilot package broad rollout karari vermez.

Bu nedenle `acceptance_status` okuyusu:

- `PILOT_ONLY`
  - controlled pilot icin anlamli
  - broad rollout demek degil
- `REJECTED`
  - pilot lane'e bile alinmamali

Tek bir pilot package green metrics verse bile limited evidence nedeniyle `PILOT_ONLY` kalabilir.

## 7. Guardrail Reading

`pilot_guardrails.json` operator icin su sorulari cevaplar:

- pilot eligible mi
- broad rollout allowed mi
- max traffic ne kadar
- fairness monitoring zorunlu mu
- rollback guard gerekli mi
- dominant fail segment nerede

Bu dosya curated website copy degil; engine-owned pilot control surface'tir.

## 8. Product Truth

`product_confidence_snapshot.json` buyer/proof dili icin uretilir.

Bu artifact:

- proof verdict
- proof confidence
- headline metrics
- supporting metrics
- phase delta
- trust layer

tasir.

Pilot package'in buyer-safe kismina bakarken ana kaynak budur.

## 9. Next-Step Guidance

Output `PILOT_ONLY` ise tipik next step:

- controlled scoping review
- segment-specific guardrail review
- curated demo alignment

Output `REJECTED` ise next step:

- mapping duzelt
- missing mandatory fields'i tamamla
- guardrail fail reason'larini gider

## 10. Related Docs

- [PILOT_DATA_CONTRACT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_DATA_CONTRACT.md)
- [PILOT_PACKAGE_SCHEMA.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_PACKAGE_SCHEMA.md)
- [PILOT_READINESS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/PILOT_READINESS.md)
