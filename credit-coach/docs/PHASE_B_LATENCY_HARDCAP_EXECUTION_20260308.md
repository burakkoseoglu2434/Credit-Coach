# Phase B Execution Report - Tail Latency Hard Cap (2026-03-08)

## Kapsam
Bu fazda şu hedefler uygulandı:
- Per-customer time budget hard enforcement
- DiCE kullanımını segment ve zaman bazlı daraltma
- Candidate pool için two-stage filtreleme
- Time budget aşımında deterministic internal-only fallback

## Yapılan Kod Değişiklikleri

### 1) Hard budget + generator skip kuralları
- Dosya: `src/credit_coach/cli/run_batch_recourse_eval.py`
- Eklenenler:
  - `hard_time_budget_enforcement`
  - `min_remaining_budget_for_dice_ms`
  - `min_remaining_budget_for_rule_ms`
  - `dice_only_high_risk_denied`
  - `rule_skipped_reason`
- Davranış:
  - Kalan bütçe yetersizse DiCE atlanır.
  - Hard budget aşıldıysa rule generator atlanır.
  - Budget aşımı sonrası deterministic `internal-only` fallback uygulanır.

### 2) Two-stage candidate filtering
- Dosya: `src/credit_coach/cli/run_batch_recourse_eval.py`
- Eklenen fonksiyonlar:
  - `_plan_gate_margin(...)`
  - `_stage1_filter_candidate_pool(...)`
- Davranış:
  - Stage-1: status + gate margin + robust score ile hızlı filtre
  - Stage-2: mevcut novelty-aware prune

### 3) Search config propagation
- Dosya: `src/credit_coach/cli/run_batch_recourse_eval.py`
- `_effective_recourse_search` içinde yeni search keys propagate edildi.

### 4) Config tuning (latency-first)
- Dosya: `configs/recourse.yaml`
- Değişiklikler:
  - `per_customer_time_budget_ms: 2000` (4500 -> 2000)
  - `candidate_pool_max_size: 12` (20 -> 12)
  - `skip_dice_when_internal_approved: true`
  - `denied_dice_max_customers: 250`
  - `dice_only_high_risk_denied: true`
  - `min_remaining_budget_for_dice_ms: 350`
  - `min_remaining_budget_for_rule_ms: 120`
  - `hard_time_budget_enforcement: true`
  - `stage1_filter_multiplier: 2.0`
  - `stage1_per_source_cap: 6`

### 5) Test kapsamı
- Dosya: `tests/test_batch_candidate_diversity.py`
  - Stage1 source-cap testi eklendi.
  - Search config propagation testi eklendi.

## Test Sonuçları

- Hedefli test:
  - `pytest -q tests/test_batch_candidate_diversity.py tests/test_planner_denied_objective.py tests/test_recourse_funnel_kpis.py tests/test_kpi_contract.py tests/test_production_smoke.py`
  - Sonuç: `13 passed`

- Full test:
  - `pytest -q`
  - Sonuç: `121 passed`

## Çalıştırma Sonuçları

## Referans (A+E sonrası, B öncesi)
- Run ID: `20260308_071037_49c3bc_74d915`
- `denied_to_approved_lift = 0.1905`
- `denied_reliability_violation_rate = 0.0000`
- `latency_p95_ms = 3870.22`
- `latency_p99_ms = 5736.53`

## B sonrası
- Run ID: `20260308_071736_a7db47_43869a`
- `denied_to_approved_lift = 0.0238`
- `denied_reliability_violation_rate = 0.7317`
- `latency_p95_ms = 3217.57`
- `latency_p99_ms = 5673.69`
- `timeout_or_fallback_rate = 0.15`

## Smoke
- Run ID: `20260308_071819_a3291d_b920e5`
- Status: `NO_GO`
- Fail gate'ler:
  - `G0_BATCH_RECOURSE_KPI`
  - `G0B_RECOURSE_FUNNEL`
  - `G4_MONITORING_TELEMETRY`

## Değerlendirme
- Pozitif:
  - Tail latency'de kısmi düşüş var (`p95` ve `p99` iyileşti).
  - Bütçe kontrollü çalıştırma mekanizması başarıyla devrede.
  - Pipeline ve testler stabil.

- Negatif:
  - Lift ciddi düştü (`0.1905 -> 0.0238`).
  - Reliability violation tekrar yükseldi (`0.0 -> 0.7317`).
  - P95/P99 halen kontratın çok üstünde.

## Sonraki Teknik Adım (öneri)
Bu fazdaki config tuning latency-first olduğu için aşırı kısıtlayıcı kaldı.
Bir sonraki adımda "balanced retune" yapılmalı:
1. `dice_only_high_risk_denied` koşulunu gevşet (en azından `denied-mid` dahil).
2. High-risk weekly optimizer maliyetini düşür (hafta/action limit) ama tamamen kapatma.
3. Budget-aware internal combo azaltımı ekle (horizon/strategy adaptif küçültme).
4. 200 -> 1000 batch tuning döngüsüyle `lift >= 0.05` ve `reliability_violation <= 0.40` geri kazan.
