# Credit Coach

> Kredi alamayan müşteriye, bankanın risk iştahına ve makro koşullara göre güncellenen,
> guven aralikli (Bootstrap/Conformal CI) ve nedensel tutarli iyilestirme plani sunan koçluk sistemi.

## Teknoloji Yığını
- Python 3.11, XGBoost, SHAP, DiCE-ML
- Pydantic v2 (şemalar), SQLAlchemy + SQLite (state store)
- Streamlit (offline demo)

## Kurulum

```bash
cd credit-coach
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
```

## Haftalık Komutlar

| Hafta | Komut |
|-------|-------|
| 1 | `python -m credit_coach.cli.run_train --dry_run` |
| 2 | `python -m credit_coach.cli.run_prepare_data --config configs/default.yaml` |
| 3 | `python -m credit_coach.cli.run_train --config configs/model.yaml` |
| 6 | `python -m credit_coach.cli.run_recourse --customer_id demo` |
| 8 | `python -m credit_coach.cli.run_shock --macro_config configs/macro.yaml --model_config configs/model.yaml` |
| 9 | `python -m credit_coach.cli.run_fairness --base_config configs/default.yaml --model_config configs/model.yaml --group_feature home_ownership` |
| 9+ | `python -m credit_coach.cli.run_fairness --base_config configs/default.yaml --model_config configs/model.yaml --macro_config configs/macro.yaml --group_feature home_ownership --batch_results_csv <batch_recourse_results.csv>` |
| 10 | `python -m credit_coach.cli.run_coaching --weeks 4` |
| Ops | `python -m credit_coach.cli.run_monitoring --monitoring_config configs/monitoring.yaml` |
| Ops | `python -m credit_coach.cli.run_production_smoke` |
| Ops | `python -m credit_coach.cli.run_batch_recourse_eval --n_customers 1000` |
| Ops | `python -m credit_coach.cli.run_high_risk_ab --execute --n_customers 1000 --n_workers 5 --control_recourse_config configs/experiments/recourse_ab_control.yaml --treatment_recourse_config configs/experiments/recourse_ab_highrisk_tuned.yaml` |
| Security | `python -m credit_coach.cli.run_audit_verify` |
| Release | `python -m credit_coach.cli.run_benchmark --model_config configs/model.yaml --window_size 3 --window_step 1 --last_k_windows 3` |

## Testler

```bash
pytest
```

## API Guvenlik Notu
- `score/demo` endpoint'i `Bearer` token ister.
- Token ayari:
  - `CREDIT_COACH_API_TOKEN=<token>` veya
  - `CREDIT_COACH_API_TOKENS=token1,token2`
  - Rotation policy: `CREDIT_COACH_API_KEYS_JSON='[{"token":"...","status":"active","expires_at":"..."}]'`
  - Scope policy (opsiyonel): `configs/security.yaml -> auth.endpoint_scopes`
- Sadece lokal demo icin (onerilmez): `CREDIT_COACH_ALLOW_INSECURE_API=1`
- Rate limit ve key policy dosyasi: `configs/security.yaml`

## Önemli Kurallar
- **48 feature kilidi**: `configs/features_48.yaml` — tek kaynak
- **Config-first**: Kodda hard-code yok, her şey YAML'den
- **Traceability**: Her çıktı `artifacts/runs/<run_id>/` altında
- **B2/B3 notu**: `configs/recourse.yaml` icinde SHAP stability ve DiCE method (`random|genetic|kdtree`) parametreleri yonetilir.
- **B3 runtime notu**: DiCE methodu hata verirse (`enable_method_fallback: true`) kalan methodlar otomatik denenir; deneme detaylari `dice_telemetry.json` icine yazilir.
- **B1 notu**: Train metrikleri artik `requested_backend`, `backend_reason`, `fallback_reason` alanlarini da yazar.
- **C1 notu**: `configs/recourse.yaml -> robust` altinda `objective`, `cvar_quantile`, `min_reliability`, `min_worst_risk_margin` gate'leri yonetilir.
- **C1 ciktilari**: `plans.csv` artik `robust_score`, `robust_margin`, `robust_anchor_pd`, `robust_worst_risk_margin` alanlarini da icerir.
- **Recourse redesign notu**: `denied_target`, `adaptive_steps`, `fairness` ve `robust.gate_objective` ayarlari ile gate-pass odakli arama aktif edilir.
- **Search budget notu**: `configs/recourse.yaml -> action_budget` ve `search_budget` ile plan aksiyon limiti, candidate pruning ve dice skip politikasi yonetilir.
- **Feasibility notu**: `configs/recourse.yaml -> feasibility` ve `configs/recourse_feasibility.yaml` ile feature bazli uygulanabilirlik kontrati (delta/aylik cap/freeze) zorunlu uygulanir.
- **Funnel ciktilari**: `run_batch_recourse_eval` artik `recourse_funnel_summary.csv`, `latency_outliers.csv` ve `batch_fairness_change.csv` uretir.
- **Batch extra ciktilari**: `recourse_action_count_distribution.csv`, `recourse_cost_percentiles.csv`, `denied_not_approved_root_causes.csv`, `batch_run_manifest.json`, `batch_recourse_fairness.csv`.
- **Denied KPI ciktilari**: `run_batch_recourse_eval` artik `denied_gate_violation_breakdown.csv`, `denied_candidate_source_breakdown.csv`, `denied_lift_by_income_band.csv`, `denied_lift_by_risk_band.csv` da uretir.
- **Conformal notu**: `run_train` artik model klasorune `conformal_calibration.json` yazar ve manifeste `conformal_calibration_path` ekler.
- **C2 notu**: `configs/coaching.yaml -> sequential` altinda haftalik aksiyon execution/dropout/noise modeli ve dinamik replan ayarlari yonetilir.
- **C2 ciktilari**: `weekly_coaching.csv` artik `planned_actions`, `executed_actions`, `missed_actions_streak`, `replan_reasons`, `target_pd` alanlarini icerir.
- **D1 notu**: `run_benchmark` artik rolling window backtesting uretir (`benchmark_rolling_windows.csv`, `benchmark_lastk_summary.csv`).
- **D2 notu**: `run_fairness` artik `fairness_stress_matrix.csv` uretir ve high-stress fairness gap'i raporlar.
- **E1 notu**: `configs/monitoring.yaml -> telemetry` ile Prometheus/OTLP export aktif edilir; sonuc `telemetry_export.json` olarak yazilir.
- **E2 notu**: Production operasyonu ve release karar adimlari icin `docs/PROD_RUNBOOK.md` ve `docs/RELEASE_GATES.md` referans alinir.
- **Smoke test notu**: `run_production_smoke` komutu latest artifactler uzerinden gate bazli PASS/FAIL raporu (`production_smoke_report.csv/json`) uretir.
- **KPI contract notu**: `run_production_smoke` thresholdlari varsayilan olarak `configs/kpi_contract.yaml` dosyasindan alir; run altinda `kpi_snapshot.json` ve `production_smoke_report.json` icinde onceki run'a gore KPI trendi de kaydedilir.
- **Batch test notu**: `run_batch_recourse_eval` 1000+ musteri icin recourse + DiCE + fairness/stress + operasyonel metrikleri tek run altinda uretir.

## Ops Dokumanlari
- `docs/PROD_RUNBOOK.md`
- `docs/RELEASE_GATES.md`
- `docs/FEATURE_FEASIBILITY_CONTRACT.md`
