# HIGH-RISK A/B RUNBOOK (2026-03-07)

## Amac
`high` risk band denied musterilerde lift artisina odakli profilin,
mevcut profile gore etkisini olcmek.

## Profil Dosyalari
- Control: `configs/experiments/recourse_ab_control.yaml`
- Treatment: `configs/experiments/recourse_ab_highrisk_tuned.yaml`
- Treatment v2: `configs/experiments/recourse_ab_highrisk_tuned_v2.yaml`
- Treatment v3: `configs/experiments/recourse_ab_highrisk_tuned_v3.yaml`
- Treatment v5: `configs/experiments/recourse_ab_highrisk_tuned_v5.yaml`
- Treatment internal-quota (GO adayi): `configs/experiments/recourse_ab_highrisk_internal_quota45.yaml`

## Tek Komut A/B (1000 musteri)
```bash
python -m credit_coach.cli.run_high_risk_ab \
  --execute \
  --n_customers 1000 \
  --sample_seed 42 \
  --n_workers 5 \
  --log_every 100 \
  --base_config configs/default.yaml \
  --model_config configs/model.yaml \
  --causality_config configs/causality.yaml \
  --safety_config configs/safety.yaml \
  --macro_config configs/macro.yaml \
  --control_recourse_config configs/experiments/recourse_ab_control.yaml \
  --treatment_recourse_config configs/experiments/recourse_ab_highrisk_tuned.yaml
```

## Tek Komut A/B (1000 musteri, v2)
```bash
python -m credit_coach.cli.run_high_risk_ab \
  --execute \
  --n_customers 1000 \
  --sample_seed 42 \
  --n_workers 5 \
  --log_every 100 \
  --base_config configs/default.yaml \
  --model_config configs/model.yaml \
  --causality_config configs/causality.yaml \
  --safety_config configs/safety.yaml \
  --macro_config configs/macro.yaml \
  --control_recourse_config configs/experiments/recourse_ab_control.yaml \
  --treatment_recourse_config configs/experiments/recourse_ab_highrisk_tuned_v2.yaml
```

## Ciktilar
Yeni A/B run altinda:
- `ab_high_risk_summary.json`
- `ab_high_risk_metric_deltas.csv`
- `ab_high_risk_riskband_deltas.csv`
- `ab_control_run.log`
- `ab_treatment_run.log`

## Mevcut Sanity Run (200 musteri)
- A/B run: `artifacts/runs/20260307_173348_31398d_c0053e`
- Control run: `20260307_173306_62bcfb_9082e5`
- Treatment run: `20260307_173330_702862_4849ad`

Ozet:
- `denied_to_approved_lift`: `+0.1190` (treatment-control)
- `denied_high_risk_lift`: `+0.1000`
- `latency_p99_ms`: `-404.38` ms
- Risk band lift:
  - `high`: `+0.1000`
  - `mid`: `+0.3333`
  - `near`: `+0.1111`

Not:
- Sanity run 200 sample'dir; release karari icin 1000 sample zorunlu.

## Son 1000 A/B (v2) Ozet
- A/B run: `artifacts/runs/20260307_223725_0e3c80_713f3b`
- Control run: `20260307_223529_df1dd8_2e41b7`
- Treatment v2 run: `20260307_223613_e9b4c6_c25dc6`

Metrik:
- `denied_to_approved_lift`: `0.01688 -> 0.05063` (hedef gecildi)
- `denied_high_risk_lift`: `0.00000 -> 0.03371`
- `latency_p95_ms`: `523.57 -> 2545.69` (FAIL)
- `latency_p99_ms`: `5340.49 -> 4024.70` (iyilesme var ama hala FAIL)
- `equalized_odds_gap_delta`: `+0.00977` (G0 limiti icinde)

Durum:
- `NO_GO` (tek ana neden latency kapilari)

## Son 1000 A/B (v3) Ozet
- A/B run: `artifacts/runs/20260307_224210_1bb750_a6ca6c`
- Control run: `20260307_224036_df1dd8_ba8a92`
- Treatment v3 run: `20260307_224129_9e26d5_5f2510`

Metrik:
- `denied_to_approved_lift`: `0.00422 -> 0.00000` (kotu)
- `denied_high_risk_lift`: `0.00000 -> 0.00000`
- `latency_p95_ms`: `453.06 -> 1019.07` (iyilesmedi, FAIL)
- `latency_p99_ms`: `4959.51 -> 2903.82` (iyilesme var ama FAIL)

Durum:
- `NO_GO`
- v3 ayarlari lift'i asiri baskiladi; denied segmentte DiCE etkinligi sifira indi.

## Son 200 A/B (v4) Sanity
- A/B run: `artifacts/runs/20260307_225333_262791_270746`
- Control run: `20260307_225246_62bcfb_d0bc4a`
- Treatment v4 run: `20260307_225321_76f208_5efcad`

Metrik:
- `denied_to_approved_lift`: `0.07143 -> 0.00000` (ciddi kotulesme)
- `latency_p95_ms`: `3136.44 -> 1320.92` (iyilesme var, hala FAIL)
- `latency_p99_ms`: `4025.98 -> 1493.24` (PASS seviyesine indi)

Durum:
- v4 latency'i iyilestirdi ancak lift'i sifirladigi icin 1000 kosu yapilmadi.

## Uygulanan Teknik Duzeltmeler (v5+)
- DiCE adapter: `kdtree` backend icin `random_seed` imza uyumlulugu duzeltildi.
- DiCE hedef hizasi: `stopping_threshold=tau` gecilerek CF arama gate esigi ile hizalandi.
- Internal hedefleme bugfix: `aggressive` hedef PD, `conservative`'dan daha guclu olacak sekilde duzeltildi.
- Denied-target quota eklendi: `search_budget.denied_target_max_customers` ile agresif denied mode sadece secili alt-kumeye uygulanabilir hale geldi.

## Tek Komut A/B (1000 musteri, internal-quota)
```bash
python -m credit_coach.cli.run_high_risk_ab \
  --execute \
  --n_customers 1000 \
  --sample_seed 42 \
  --n_workers 5 \
  --log_every 100 \
  --base_config configs/default.yaml \
  --model_config configs/model.yaml \
  --causality_config configs/causality.yaml \
  --safety_config configs/safety.yaml \
  --macro_config configs/macro.yaml \
  --control_recourse_config configs/experiments/recourse_ab_control.yaml \
  --treatment_recourse_config configs/experiments/recourse_ab_highrisk_internal_quota45.yaml
```

## Son 1000 A/B (internal-quota45) Ozet
- A/B run: `artifacts/runs/20260307_232008_a7f607_e9eaf3`
- Control run: `20260307_231902_df1dd8_7e165d`
- Treatment run: `20260307_231947_665d15_7ed31e`

Metrik:
- `denied_to_approved_lift`: `0.00844 -> 0.08861` (PASS)
- `denied_high_risk_lift`: `0.00000 -> 0.00000`
- `latency_p95_ms`: `385.59 -> 354.96` (PASS)
- `latency_p99_ms`: `5858.62 -> 1883.39` (PASS)
- `error_rate`: `0.0000 -> 0.0000` (PASS)
- `fairness_approval_gap_after`: `0.09983 -> 0.09807` (PASS)

Durum:
- `GO` (A/B summary: treatment `all_pass = true`)
- Lift artik internal planner'dan geliyor; denied segmentte `internal_only` payi belirgin sekilde artti.

## Production Smoke (batch-aligned replay) Sonucu
- Benchmark run: `20260307_233437_765142_1d744f`
- Fairness run: `20260307_233440_ecb8c8_5d3b94`
- Shock run: `20260307_233438_f3a27e_dd71d5`
- Monitoring run: `20260307_233441_07f77f_88fb6b`
- Smoke run: `20260307_233442_2a1df3_2ccf15`

Ozet:
- `NO_GO` (tek fail: `G0.equalized_odds_gap_delta`)
- Fail metrik: `equalized_odds_gap_delta = +0.0210` (esik `<= +0.01`)

Not:
- G1, G2, G3, G4, G5 pass.
- Batch KPI tarafinda lift/latency/error/fairness gap pass; sadece EO delta limiti asiliyor.

## Model-Side Uncertainty Upgrade (2026-03-08)
- `safety/statistical.py` icine score-bin tabanli adaptif conformal width eklendi.
- `run_train.py` conformal artifact'ine `score_bin_edges/widths/gaps` metadata yazacak sekilde guncellendi.
- Batch/recourse CLI'da calibration path inject bugfix yapildi (`""` ise manifest path zorlanir).

Not:
- Bu turde xgboost egitimi ortam kaynakli `OMP SHM` hatasi verdigi icin
  model egitimi `CREDIT_COACH_FORCE_BACKEND=logistic_regression` ile tamamlandi.

## Final Treatment Profili (GO)
- Treatment config: `configs/experiments/recourse_ab_highrisk_internal_q30_tb700_adaptive.yaml`
- Temel farklar:
  - `search_budget.per_customer_time_budget_ms: 700`
  - `search_budget.denied_target_max_customers: 30`
  - uncertainty adaptive mode aktif (`adaptive_by_score=true`, `max_width=0.08`)

## Son 1000 A/B (adaptive q30/tb700) Ozet
- A/B run: `artifacts/runs/20260308_010804_1d403c_e72fd1`
- Control run: `20260308_010659_77751a_12f9fa`
- Treatment run: `20260308_010749_837f33_55b99a`

Metrik:
- `denied_to_approved_lift`: `0.03797 -> 0.09283` (PASS)
- `latency_p95_ms`: `486.56 -> 286.88` (PASS)
- `latency_p99_ms`: `6422.82 -> 1573.52` (PASS)
- `fairness_approval_gap_after`: `0.10045 -> 0.08435` (PASS)
- `error_rate`: `0.0000 -> 0.0000` (PASS)

Durum:
- A/B summary: treatment `all_pass = true`

## Final Production Smoke (GO)
- Benchmark run: `20260308_010840_edfcb0_fe7589`
- Fairness run: `20260308_010842_ecb8c8_a9af0f`
- Shock run: `20260308_010843_f3a27e_66c3bc`
- Monitoring run: `20260308_010844_07f77f_e10816`
- Smoke run: `20260308_010845_0ed7c7_a7319d`

Smoke gate ozet:
- `G0_BATCH_RECOURSE_KPI`: PASS
- `G1_MODEL_BACKTEST`: PASS
- `G2_FAIRNESS`: PASS
- `G3_ROBUSTNESS`: PASS
- `G4_MONITORING_TELEMETRY`: PASS
- `G5_SECURITY_AUDIT`: PASS

Nihai karar:
- `GO`
