# CREDIT COACH RELEASE GATES

## 1) Amac
Bu dokuman production release oncesi zorunlu Go/No-Go kapilarini tanimlar.

## 2) Girdi Artifactleri
1. Benchmark:
   - `benchmark_comparison.csv`
   - `benchmark_lastk_summary.csv`
2. Fairness:
   - `fairness_report.csv`
   - `fairness_stress_matrix.csv`
3. Shock:
   - `shock_reliability.csv`
4. Monitoring:
   - `monitoring_summary.csv`
   - `monitoring_alerts.csv`
   - `telemetry_export.json`
5. Batch recourse:
   - `batch_summary.json`
   - `batch_run_manifest.json`
   - `batch_fairness_change.csv`
   - `batch_recourse_fairness.csv`
   - `recourse_funnel_summary.csv`
   - `denied_not_approved_root_causes.csv`
   - `recourse_action_count_distribution.csv`
   - `recourse_cost_percentiles.csv`
   - `latency_outliers.csv`

## 3) Zorunlu Kapilar
### G0 - Batch recourse KPI contract
1. `denied_to_approved_lift >= 0.05`
2. `approval_gap_delta <= +0.01`
3. `equalized_odds_gap_delta <= +0.01`
4. `latency_p95_ms <= 500`
5. `latency_p99_ms <= 2000`
6. `error_rate <= 0.005`
7. `recourse_success_gap <= 0.10`
8. `recourse_cost_gap <= 500`

### G1 - Model ve recourse performansi
1. `our_last_k_validity >= 0.85`
2. `our_last_k_safe_rate >= 0.60`
3. `our_last_k_avg_risk_margin >= 0.00`

### G2 - Fairness
1. `approval_gap <= 0.10`
2. `equalized_odds_gap <= 0.10`
3. `high_stress_fairness_gap <= 0.10`

### G3 - Robustness ve stress
1. `avg_reliability >= 0.70`
2. `min_robust_margin` negatif patlamaya girmemeli (urune ozel esik)

### G4 - Drift ve izleme
1. `max_psi <= 0.20`
2. `HIGH alert count == 0`
3. Telemetry export `exported=true` (enabled ortamlar icin)

### G5 - Guvenlik ve audit
1. API auth aktif
2. Rate limit aktif
3. Audit hash chain verify PASS

## 4) Go/No-Go Formu
Asagidaki tablo doldurulmadan release etiketi verilmez:

| Gate | Durum | Kanit Dosyasi | Not |
|---|---|---|---|
| G0 Batch KPI | PASS/FAIL | batch_summary.json, batch_run_manifest.json, batch_fairness_change.csv, recourse_funnel_summary.csv |  |
| G1 Model/Recourse | PASS/FAIL | benchmark_lastk_summary.csv |  |
| G2 Fairness | PASS/FAIL | fairness_report.csv, fairness_stress_matrix.csv |  |
| G3 Stress | PASS/FAIL | shock_reliability.csv, monitoring_summary.csv |  |
| G4 Monitoring | PASS/FAIL | monitoring_summary.csv, monitoring_alerts.csv, telemetry_export.json |  |
| G5 Security/Audit | PASS/FAIL | security test raporu, run_audit_verify cikti |  |

## 5) Karar Kurali
1. Tum gate'ler PASS ise: `GO`
2. En az bir gate FAIL ise: `NO-GO`
3. Kosullu release (waiver) yalnizca yazili risk onayi ile mumkun.

## 6) Dry-Run Proseduru
Release oncesi zorunlu dry-run:
```bash
pytest -q
TQDM_DISABLE=1 python -m credit_coach.cli.run_batch_recourse_eval --n_customers 1000 --sample_seed 42
python -m credit_coach.cli.run_benchmark --model_config configs/model.yaml --window_size 3 --window_step 1 --last_k_windows 3
python -m credit_coach.cli.run_fairness --base_config configs/default.yaml --model_config configs/model.yaml --macro_config configs/macro.yaml --group_feature home_ownership
python -m credit_coach.cli.run_shock --macro_config configs/macro.yaml --model_config configs/model.yaml
python -m credit_coach.cli.run_monitoring --base_config configs/default.yaml --monitoring_config configs/monitoring.yaml
python -m credit_coach.cli.run_audit_verify
python -m credit_coach.cli.run_production_smoke
```

## 7) Rollback Hazirlik Checklist
1. Son stabil model versiyonu etiketli mi?
2. Rollback sorumlusu ve onay zinciri net mi?
3. Rollback komutlari test ortaminda calisti mi?
4. Incident iletisim kanali hazir mi?

## 8) Kayit Tutma
Her release icin su dosyalar saklanir:
1. Go/No-Go formu
2. Artifact run_id listesi
3. Onay veren kisiler
4. Release tarihi/surumu
