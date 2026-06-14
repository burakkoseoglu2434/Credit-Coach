# Pilot Execution Guide

Bu runbook, Phase 44 sonrasi pilot baseline'in nasil tekrar calistirilacagini tanimlar.

Bu guide'in anlattigi sey:

- controlled
- governed
- repeatable
- versioned
- bounded

pilot baseline'dir.

Bu guide su iddialari tasimaz:

- live integration
- self-serve pilot
- compliance automation
- autonomous adjudication

## 1. Canonical Command

Phase 44 sonrasi canonical refresh komutu:

```bash
cd credit-coach
python -m credit_coach.cli.run_pilot_baseline_refresh \
  --pilot_bundle /absolute/path/to/pilot_bundle.json
```

Ince overlay'ler gerekiyorsa:

- `--institution_policy`
- `--institution_offer`
- `--pilot_profile`

Opsiyonel refresh posture override'lari:

- `--cadence_mode`
- `--cohort_policy`
- `--n_customers`
- `--sample_seed`
- `--reference_run_id`
- `--reference_label`

## 2. Cadence Contract

Refresh scheduler zorunlu degildir.
Ama cadence posture explicit olmalidir.

Canonical mode'lar:

- `pre_pilot`
- `weekly_during_pilot`
- `pre_readout`

Kural:

- refresh operator-triggered olabilir
- ama cadence mode manifest ve summary'de acikca yazilmalidir

## 3. Runtime Flow

`run_pilot_baseline_refresh` yeni karar mantigi yazmaz.
Mevcut truth-owner runner'lari siraya koyar:

1. pilot bundle normalize edilir
2. `run_customer_artifact_collection` calisir
3. collection raw/operator truth'unden `decision_explanation_pack` uretilir
4. `run_pilot_integration` pilot package'i yeniler
5. `run_production_smoke` portfolio smoke lane'ini calistirir
6. `run_pilot_artifact_qa` artifact trust lane'ini degerlendirir
7. reference run varsa version comparison yazilir

Kural:

- new orchestrator
- no new engine

## 4. Dual-Lane Reading

Phase 44 refresh output'u iki farkli gate tasir:

- `portfolio_smoke_status`
- `artifact_qa_status`

### Portfolio smoke

Su soruya cevap verir:

- is degeri ve release posture kabul edilebilir mi

### Artifact QA

Su soruya cevap verir:

- paket eksiksiz, tutarli ve non-leaky mi

Kural:

- smoke = business / release lane
- artifact QA = trust / packaging lane

Ikisi tek statuye indirgenmez.

## 5. QA Outcome Vocabulary

Artifact QA sonucu yalnizca su setten gelir:

- `PASS`
- `DEGRADED`
- `FAIL`

Okuma:

- `PASS`
  - pilot paketi guvenle okunabilir
- `DEGRADED`
  - paket kullanilabilir ama watchlist notu vardir
- `FAIL`
  - pilot baseline acceptance bloklanir

## 6. Reference Run Comparison

Canonical comparison posture:

- current refresh
- vs
- same institution profile icin previous approved pilot baseline

Eger boyle bir run yoksa:

- explicit `reference_run_id` kullanilabilir
- ama comparison `non-canonical` olarak etiketlenir

Bu ayrim sessizce yanlis baseline secilmesini engeller.

## 7. Overlay Precedence

Institution overlay precedence sabittir:

1. base configs
2. institution overlays
3. pilot bundle context
4. explicit CLI override

Resolve edilmis runtime config refresh manifest icinde gorunur kalmalidir.

## 8. Core Outputs

Phase 44 refresh altinda minimum beklenen artifact'ler:

- `tables/pilot_refresh_manifest.json`
- `tables/pilot_refresh_summary.md`
- `tables/policy_version_comparison.csv`
- `tables/policy_version_comparison.md`
- `tables/artifact_qa_summary.json`
- `tables/release_smoke_summary.json`
- `tables/refresh_context.json`
- `tables/decision_explanation_packs/`

## 9. First Read Order

Bir refresh bittiğinde sirali okuma:

1. `pilot_refresh_summary.md`
2. `artifact_qa_summary.json`
3. `release_smoke_summary.json`
4. `pilot_refresh_manifest.json`
5. `policy_version_comparison.md`

Sonra gerekiyorsa:

- collection run
- pilot package
- operator packets
- explanation packs

## 10. Institution-Facing Boundary

Institution-facing artifact'ler su truth'leri kullanir:

- external decision only
- owned one-line reason
- numeric drivers
- upgrade condition
- expected readiness

Su truth'ler dis yuzeye cikmaz:

- `NEEDS_REVIEW`
- raw gate trace
- candidate policy tables
- debug dumps

## 11. Related Docs

- [PILOT_DATA_CONTRACT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_DATA_CONTRACT.md)
- [PILOT_PACKAGE_SCHEMA.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/PILOT_PACKAGE_SCHEMA.md)
- [DECISION_EXPLANATION_PACK.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/docs/DECISION_EXPLANATION_PACK.md)
- [PILOT_READINESS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/PILOT_READINESS.md)
