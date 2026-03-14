# Phase B Balanced Retune Report (2026-03-08)

## Amaç
Latency hard-cap sonrası fazla düşen lift/reliability metriklerini geri kazanmak ve latency kazanımını korumak.

## Uygulanan Ek Değişiklikler

### Kod
- `src/credit_coach/cli/run_batch_recourse_eval.py`
  - `_effective_recourse_search` içine regular profil eklendi:
    - `regular_horizons`
    - `regular_strategies`
    - `regular_topk`
  - Amaç: non-denied popülasyonda iç arama kombinasyonunu küçültüp latency yükünü azaltmak.

### Config
- `configs/recourse.yaml` (balanced retune)
  - `per_customer_time_budget_ms: 2800`
  - `candidate_pool_max_size: 14`
  - `stage1_filter_multiplier: 1.8`
  - `stage1_per_source_cap: 8`
  - `regular_horizons: [3, 6]`
  - `regular_strategies: [conservative]`
  - `regular_topk: 8`
  - `denied_dice_max_customers: 320`
  - `dice_only_high_risk_denied: false`
  - `min_remaining_budget_for_dice_ms: 220`
  - `min_remaining_budget_for_rule_ms: 80`
  - `high_risk_profile.weekly_weeks: 12`
  - `high_risk_profile.weekly_max_actions: 2`
  - `high_risk_profile.max_actions: 10`

### Test
- `tests/test_batch_candidate_diversity.py`
  - regular profile propagation testi eklendi.

## Test Sonuçları
- Targeted suite: `13 passed`
- Full suite: `121 passed`

## Çalıştırmalar

## Referans B run (hard-cap ilk hali)
- Run ID: `20260308_071736_a7db47_43869a`
- `denied_to_approved_lift = 0.0238`
- `denied_reliability_violation_rate = 0.7317`
- `latency_p95_ms = 3217.57`
- `latency_p99_ms = 5673.69`

## Balanced retune run
- Run ID: `20260308_072238_31b2e8_21786d`
- `denied_to_approved_lift = 0.0476`
- `denied_reliability_violation_rate = 0.5750`
- `latency_p95_ms = 3035.11`
- `latency_p99_ms = 20317.23`

## Delta (balanced - B)
- `denied_to_approved_lift`: `+0.0238` (iyileşti)
- `denied_reliability_violation_rate`: `-0.1567` (iyileşti)
- `latency_p95_ms`: `-182.46 ms` (iyileşti)
- `latency_p99_ms`: `+14643.54 ms` (kötüleşti, tail outlier)

## Smoke
- Run ID: `20260308_072340_f7de76_a41955`
- `overall_status = NO_GO`
- Fail gate'ler:
  - `G0_BATCH_RECOURSE_KPI` (lift<0.05, latency p95/p99 fail)
  - `G0B_RECOURSE_FUNNEL` (gate_pass_rate<0.08, reliability_violation>0.40)
  - `G4_MONITORING_TELEMETRY` (telemetry disabled)

## Değerlendirme
- Balanced retune, hard-cap'e göre iş KPI'larını toparladı ama hedefe yetmedi.
- p99 tail'de ciddi outlier sorunu var; bu tek başına release blocker.
- Reliability tarafı iyileşti ama halen kontrat dışı.

## Sonraki Teknik Adım (öneri)
1. `p99` için "strict tail guard":
   - DiCE timeout üst limiti daha düşük ve tek-attempt moduna geçirilmeli.
   - Timeout sonrası anında internal deterministic seçim (tek plan) yapılmalı.
2. `denied_reliability_violation_rate` için:
   - denied objective ağırlıkları tekrar reliability/ci yönüne çekilmeli.
   - high-risk denied için minimum gate marjı odaklı rerank zorunlu kılınmalı.
3. 200 müşteri hızlı tuning döngüsü (3-4 iterasyon) sonrası 1000 batch final.
