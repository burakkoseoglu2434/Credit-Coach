# Batch 1000 Scale Report - Tail Guard Config (2026-03-08)

## Çalıştırma
- Batch run: `20260308_072902_794a1a_1704ca`
- Smoke run: `20260308_073158_acda26_f2ec40`
- Komut: `python -m credit_coach.cli.run_batch_recourse_eval --n_customers 1000 ...`

## KPI Özeti (1000 müşteri)
- `denied_count = 237`
- `denied_with_gate_pass_plan = 7`
- `denied_to_approved_lift = 0.0295`
- `denied_high_risk_lift = 0.0056`
- `denied_reliability_violation_rate = 0.8000`
- `latency_p95_ms = 3557.47`
- `latency_p99_ms = 4034.68`
- `elapsed_total_s = 153.21`

## Smoke Sonucu
- `overall_status = NO_GO`

Fail gate'ler:
- `G0_BATCH_RECOURSE_KPI`
  - `denied_to_approved_lift < 0.05`
  - `latency_p95_ms > 500`
  - `latency_p99_ms > 2000`
- `G0B_RECOURSE_FUNNEL`
  - `denied_gate_pass_rate < 0.08`
  - `denied_reliability_violation_rate > 0.40`
- `G4_MONITORING_TELEMETRY`
  - telemetry disabled

## 200 vs 1000 Gözlemi
Aynı config 200 müşteride daha iyi görünürken 1000 müşteride düşüş var:
- Lift ve denied gate-pass oranı ölçekte belirgin düşüyor.
- Reliability violation oranı ölçekte yeniden yükseliyor.
- p95/p99 hedefin çok üstünde kalıyor.

Bu, config'in küçük örneklemde "kısmi" çalıştığını ama geniş dağılımda robust olmadığını gösteriyor.

## Teknik Yorum
1. Denied segment içinde zor vakalar arttıkça mevcut aday üretimi gate-pass plan bulamıyor.
2. Tail guard p99'u tekil outlierlardan koruyor ama genel p95 seviyesini release limitine indirecek kadar agresif değil.
3. High-risk alt segment için objective ve action search hâlâ yetersiz.

## Sonraki Adım Önerisi
1. High-risk denied için ayrı planner budget ve objective (CI/reliability ağırlıklı).
2. Denied için iki aşamalı arama: hızlı gate-pass araması + yalnızca umutlu adaylarda genişletilmiş arama.
3. 1000 run'a geçmeden önce 300-400 müşteri üzerinde risk-band bazlı tuning grid.
