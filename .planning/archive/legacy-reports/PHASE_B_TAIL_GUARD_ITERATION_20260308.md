# Phase B Tail-Guard Iteration Report (2026-03-08)

## Amaç
Balanced retune sonrası p99 tail outlier problemini çözmek.

## Yapılan Değişiklikler

### Kod
- `src/credit_coach/cli/run_batch_recourse_eval.py`
  - `hard_max_dice_timeout_ms` search config alanı eklendi.
  - Hard budget modunda DiCE timeout zorunlu hale getirildi:
    - `dice.timeout_ms=0` olsa bile kalan bütçe üzerinden timeout atanıyor.
  - Timeout üstüne ayrıca `hard_max_dice_timeout_ms` clamp uygulanıyor.

### Config
- `configs/recourse.yaml`
  - `dice.timeout_ms: 1500`
  - `search_budget.hard_max_dice_timeout_ms: 1200`

### Test
- `tests/test_batch_candidate_diversity.py`
  - Yeni config anahtarı propagation doğrulandı.

## Test Sonuçları
- Targeted suite: `13 passed`
- Full suite: `121 passed`

## Ölçüm Karşılaştırması

## Önceki balanced run
- Run: `20260308_072238_31b2e8_21786d`
- `denied_to_approved_lift = 0.0476`
- `denied_reliability_violation_rate = 0.5750`
- `latency_p95_ms = 3035.11`
- `latency_p99_ms = 20317.23`
- `elapsed_total_s = 55.83`

## Tail-guard sonrası run
- Run: `20260308_072546_6f7d95_a22ab9`
- `denied_to_approved_lift = 0.0476`
- `denied_reliability_violation_rate = 0.1500`
- `latency_p95_ms = 2488.78`
- `latency_p99_ms = 3088.45`
- `elapsed_total_s = 19.40`

## Delta
- `denied_to_approved_lift`: `+0.0000`
- `denied_reliability_violation_rate`: `-0.4250` (ciddi iyileşme)
- `latency_p95_ms`: `-546.32 ms`
- `latency_p99_ms`: `-17228.79 ms` (çok ciddi iyileşme)
- `elapsed_total_s`: `-36.43 s`

## Smoke Sonucu
- Run: `20260308_072610_f32f25_ca6b1a`
- `overall_status = NO_GO`

Fail eden kritik noktalar:
- `G0_BATCH_RECOURSE_KPI`
  - `denied_to_approved_lift < 0.05`
  - `latency_p95_ms > 500`
  - `latency_p99_ms > 2000`
- `G0B_RECOURSE_FUNNEL`
  - `denied_gate_pass_rate < 0.08`
- `G4_MONITORING_TELEMETRY`
  - telemetry disabled

## Değerlendirme
- Tail-guard değişikliği p99/p95 ve toplam süreyi anlamlı düşürdü.
- Reliability violation kontrat altına indi (`0.15 <= 0.40`).
- Ancak lift/gate_pass_rate hâlâ hedefin az altında kaldı (`0.0476 < 0.05`, `0.0476 < 0.08`).
- Latency hedefleri hâlâ uzak (`p95 2488`, `p99 3088`).

## Sonraki Adım
1. Denied segmentte gate-pass odaklı aday üretimi artır (özellikle `near/mid` risk band için düşük maliyetli ek plan).
2. High-cost denied vakalarda plan sayısını düşürüp tek-shot internal optimization dene (latency için).
3. Telemetry prod profile zorunluluğu için monitoring exporter'ı gerçek endpoint ile aktive et.
