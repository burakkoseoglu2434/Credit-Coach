# Phase B v2 GO Report (2026-03-08)

## Scope
Bu iterasyonda iki ana hedef tamamlandı:
1. `denied_to_approved_lift` ve `denied_gate_pass_rate` KPI eşiklerini 1000 müşteri batch'te geçmek.
2. Telemetry gate'ini (`G4`) prod smoke'ta geçecek şekilde aktif/denetlenebilir hale getirmek.

## Uygulanan Değişiklikler

### 1) Recourse tuning (v2)
- Yeni config: `configs/experiments/recourse_phaseb_hybrid_v2.yaml`
- Ana tuning noktaları:
  - Denied distance profile near/mid aramasını güçlendirme
  - Denied target quota artırımı (`70`)
  - Fairness tabanlı denied seçiminde mixed-share yaklaşımı
  - Hard budget + strict latency guard korunumu

### 2) Telemetry exporter hardening
- Kod: `src/credit_coach/ops/telemetry.py`
  - Yeni `mode: file` desteği eklendi.
  - Telemetry payload dosyaya yazılarak `status=success` ve `exported=true` üretilebiliyor.
- Test: `tests/test_telemetry_export.py`
  - `file` export modu için yeni test eklendi.
- Config:
  - `configs/monitoring.yaml` yorum satırı `file` modunu içerecek şekilde güncellendi.
  - `configs/experiments/monitoring_telemetry_file.yaml` eklendi.

### 3) Monitoring CLI alignment
- Kod: `src/credit_coach/cli/run_monitoring.py`
  - `batch_summary_json` verildiğinde aynı run içindeki `batch_recourse_results.csv` otomatik plan kaynağı olarak kullanılabiliyor.
  - `best_status -> status`, `best_worst_risk_margin -> risk_margin` normalize adımı eklendi.
  - Böylece monitoring approval rate metriği batch sonuçlarıyla uyumlu hesaplanıyor.

## Validasyon Sonuçları

### Batch (1000) - v2 recourse
- Run: `20260308_144830_19e083_758ca0`
- `denied_to_approved_lift = 0.1097`
- `denied_gate_pass_rate = 0.1097`
- `denied_reliability_violation_rate = 0.0379`
- `latency_p95_ms = 430.32`
- `latency_p99_ms = 1331.38`
- `error_rate = 0.0`

### Monitoring + telemetry (file mode)
Run: `20260308_144852_6db8cf_6e39a3`
- `approval_rate = 0.785`
- `max_psi = 0.00536`
- Telemetry: `enabled=true`, `status=success`, `exported=true`, `send_success_rate=1.0`

### Production smoke (explicit artifacts)
- Run: `20260308_144901_934f4b_05231d`
- Sonuç: `GO`
- Gate durumu:
  - `G0 PASS`
  - `G0B PASS`
  - `G1 PASS`
  - `G2 PASS`
  - `G3 PASS`
  - `G4 PASS`
  - `G5 PASS`

## Kalan Teknik Risk (Açık)
- `denied_high_risk_lift = 0.0` (high-risk segment dönüşümü hâlâ yok)
- Dönüşüm near-band denied üzerinde yoğunlaşıyor; high-risk için ayrı ürün/policy tasarımı gerekmeye devam ediyor.

## High-risk Denemesi (Rollback Notu)
- High-risk lift'i artırmak için `loan_amnt/funded_amnt/installment/int_rate` aksiyonları geçici olarak açıldı.
- Sonuç: `denied_high_risk_lift` artmadı, toplam lift/latency dengesi bozuldu.
- Karar: Bu değişiklikler geri alındı, stabil `v2 + telemetry-file` baseline korundu.

## Çalıştırma Komutları (Repro)
```bash
# 1) Batch recourse (v2)
TQDM_DISABLE=1 python -m credit_coach.cli.run_batch_recourse_eval \
  --n_customers 1000 \
  --sample_seed 42 \
  --log_every 100 \
  --n_workers 5 \
  --base_config configs/default.yaml \
  --model_config configs/model.yaml \
  --recourse_config configs/experiments/recourse_phaseb_hybrid_v2.yaml \
  --causality_config configs/causality.yaml \
  --safety_config configs/safety.yaml \
  --macro_config configs/macro.yaml

# 2) Monitoring + telemetry (file exporter)
python -m credit_coach.cli.run_monitoring \
  --base_config configs/default.yaml \
  --monitoring_config configs/experiments/monitoring_telemetry_file.yaml \
  --batch_summary_json artifacts/runs/<BATCH_RUN_ID>/tables/batch_summary.json

# 3) Production smoke
python -m credit_coach.cli.run_production_smoke \
  --kpi_contract configs/kpi_contract.yaml \
  --batch_summary_json artifacts/runs/<BATCH_RUN_ID>/tables/batch_summary.json \
  --batch_fairness_change_csv artifacts/runs/<BATCH_RUN_ID>/tables/batch_fairness_change.csv \
  --monitoring_summary_csv artifacts/runs/<MON_RUN_ID>/tables/monitoring_summary.csv \
  --telemetry_json artifacts/runs/<MON_RUN_ID>/tables/telemetry_export.json
```
