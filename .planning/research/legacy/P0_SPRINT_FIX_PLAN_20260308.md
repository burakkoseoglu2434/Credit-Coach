# P0 Sprint Fix Plan (2026-03-08)

Bu plan, son geliştirme raporlarında görülen 4 kritik üretim engelini kapatmak için hazırlanmıştır:
- Reliability gate tıkanması
- Tail latency patlaması
- Fairness regresyonu
- Telemetry zorunluluğu drift'i

Amaç: Lift kazanımını koruyup sistemi tekrar release-gate uyumlu hale getirmek.

## 0) Başlangıç Referansı (Baseline)

Referans run: `20260308_063829_2d920a_c4c731`
- `denied_to_approved_lift = 0.2321`
- `denied_high_risk_lift = 0.1236`
- `denied_reliability_violation_rate = 1.0`
- `latency_p95_ms = 3362.98`
- `latency_p99_ms = 40170.64`
- `fairness_equalized_odds_gap_after = 0.1771`
- `fairness_multi_max_equalized_odds_gap_after = 0.9950`
- `fairness_segment_coverage_rate = 0.5833`
- `denied_not_approved_top_root_cause = reliability_gate (1.0)`

Hedef KPI kontratı (P0 için):
- `min_denied_to_approved_lift >= 0.05`
- `max_p95_latency_ms <= 500`
- `max_p99_latency_ms <= 2000`
- `max_equalized_odds_gap_delta <= 0.01`
- `max_fairness_gap <= 0.10`
- `require_telemetry_enabled = true`
- Ek P0 recourse funnel gate:
  - `denied_reliability_violation_rate <= 0.40`
  - `denied_with_gate_pass_plan / denied_count >= 0.08`

## 1) Workstream A - Reliability Gate De-Blocking

### Problem
`denied_reliability_violation_rate=1.0` ve root cause tamamen reliability gate.

### Kod değişiklik alanları
- `src/credit_coach/recourse/generator.py`
- `src/credit_coach/coaching/planner.py`
- `src/credit_coach/safety/validator.py`
- `configs/recourse.yaml`
- `configs/safety.yaml`

### Uygulama adımları
1. Denied objective içinde reliability/worst-margin ceza ağırlıklarını risk-band'a göre yeniden dengele:
   - `risk_band=high` için reliability iyileştirmeyi ödüllendir, sadece ceza bazlı değil bonus bazlı hale getir.
2. Weekly optimizer'da `optimize_for_gate=true` akışında aday skoru yalnız PD düşüşüne değil gate-loss düşüşüne bağla (zaten var, etkisini artır).
3. `choose_best_plan` seçiminde denied modunda status sonrası tie-break'i şu sıraya sabitle:
   - gate ihlal toplamı en düşük
   - CI marjı en yüksek
   - reliability marjı en yüksek
   - maliyet/sparsity
4. Validator reason kodlarını çoklu root-cause ayrıştırma için normalize et (reliability+ci birlikte olduğunda `multi` etiketi).

### Kabul kriteri
- 1000 batch'te:
  - `denied_reliability_violation_rate <= 0.40`
  - `denied_not_approved_top_root_cause_share <= 0.70`
  - `denied_to_approved_lift >= 0.08`

### Testler
- Yeni test: denied objective sıralaması gate-loss odaklı mı?
- Yeni test: mixed violation durumunda root cause doğru sınıflanıyor mu?
- Var olan testler:
  - `tests/test_recourse_funnel_kpis.py`

## 2) Workstream B - Tail Latency Hard Cap

### Problem
`p95/p99` release sınırının çok üstünde; özellikle DiCE ve geniş candidate pool tail'i büyütüyor.

### Kod değişiklik alanları
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `src/credit_coach/recourse/dice_baseline.py`
- `configs/recourse.yaml`

### Uygulama adımları
1. Per-customer budget enforcement'ı hard yap:
   - Internal plan üretiminden sonra kalan süre < eşik ise DiCE tamamen skip.
   - DiCE timeout, kalan sürenin %X'i ile clamp.
2. `risk_band=high + denied` dışında DiCE quota'yı daralt.
3. Candidate pool prune'u iki aşamalı yap:
   - Stage-1 hızlı filtre (status/gate margin)
   - Stage-2 novelty rerank
4. Deterministic fallback yalnız "no-candidate" değil "budget-exceeded" için de deterministic approved-likely template denesin.

### Kabul kriteri
- 1000 batch'te:
  - `latency_p95_ms <= 500`
  - `latency_p99_ms <= 2000`
  - `timeout_or_fallback_rate <= 0.10`
  - Lift kaybı kontrollü: `denied_to_approved_lift >= 0.05`

### Testler
- Yeni test: time budget aşıldığında DiCE çağrısı yapılmıyor.
- Yeni test: prune sonrası candidate_pool_max_size garanti.
- Var olan testler:
  - `tests/test_batch_candidate_diversity.py`
  - `tests/test_dice_adapter_hardening.py`

## 3) Workstream C - Fairness Regression Recovery

### Problem
EO gap ve multi-segment max EO gap belirgin kötüleşti; segment coverage düşük.

### Kod değişiklik alanları
- `src/credit_coach/evaluation/fairness.py`
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `configs/recourse.yaml`
- `configs/kpi_contract.yaml`

### Uygulama adımları
1. Multi-segment fairness setini prod profilinde zorunlu hale getir:
   - `income_band`, `risk_band`, `home_ownership`, mümkünse `age_band`.
2. Segment coverage için minimum örnek kuralı:
   - düşük örnekli segmentler "reportable=false" ama coverage metriğine yansıtılsın.
3. Denied-target quota seçiminde fairness penalty katsayılarını kalibre et:
   - Lift'i öldürmeden EO gap delta'yı sınırlayan grid-tune.
4. Batch summary'ye fairness worst-segment kimliği ve top-k kötü segmentleri ekle.

### Kabul kriteri
- 1000 batch'te:
  - `fairness_equalized_odds_gap_after <= 0.12`
  - `fairness_multi_max_equalized_odds_gap_after <= 0.25`
  - `fairness_segment_coverage_rate >= 0.80`
  - `max_equalized_odds_gap_delta <= 0.01`

### Testler
- Yeni test: fairness multi coverage hesaplaması min_segment_n davranışı.
- Yeni test: fairness worst-segment summary alanları dolu.
- Var olan testler:
  - `tests/test_multi_segment_fairness.py`

## 4) Workstream D - Telemetry Enforcement Drift Fix

### Problem
KPI kontratta telemetry zorunlu ama smoke run'da override ile kapanabiliyor.

### Kod değişiklik alanları
- `src/credit_coach/ops/kpi_contract.py`
- `src/credit_coach/cli/run_production_smoke.py`
- `configs/kpi_contract.yaml`
- `configs/monitoring.yaml`
- `tests/test_production_smoke.py`

### Uygulama adımları
1. Production smoke için profil kavramı ekle:
   - `--profile prod|dev` (prod default)
   - prod'da `allow_telemetry_disabled` reddedilsin.
2. `require_telemetry_enabled=true` ise telemetry payload'da zorunlu alan kontrolü yap:
   - `enabled=true`, `exported=true`, `status=success`, success rate, lag.
3. Monitoring config'de prod örnek dosyada telemetry `enabled:true` olacak ayrı config üret.
4. Smoke report'a `telemetry_contract_source` alanı ekle (hangi config/override ile karar verildi).

### Kabul kriteri
- Prod profile smoke:
  - telemetry kapalıysa `overall_status=NO_GO`
  - telemetry eksik alan varsa `G4=FAIL`
- Dev profile smoke:
  - mevcut esnek davranış korunabilir.

### Testler
- Yeni test: prod profile'da `--allow_telemetry_disabled` etkisiz/invalid.
- Yeni test: telemetry payload eksik alanları FAIL üretiyor.
- Var olan testler:
  - `tests/test_kpi_contract.py`
  - `tests/test_production_smoke.py`

## 5) Workstream E - KPI Contract Expansion (Recourse Funnel Gate)

### Problem
Release gate, recourse tıkanmasını doğrudan yakalayamıyor.

### Kod değişiklik alanları
- `configs/kpi_contract.yaml`
- `src/credit_coach/ops/kpi_contract.py`
- `src/credit_coach/cli/run_production_smoke.py`
- `tests/test_kpi_contract.py`
- `tests/test_production_smoke.py`

### Uygulama adımları
1. Yeni threshold key'leri ekle:
   - `max_denied_reliability_violation_rate`
   - `min_denied_gate_pass_rate`
2. `run_production_smoke` G0 veya yeni `G0B_RECOURSE_FUNNEL` içinde bu iki metriği kontrol et.
3. `batch_summary.json` -> smoke mapping'i netleştir:
   - gate_pass_rate = `denied_with_gate_pass_plan / denied_count`
4. Snapshot raporunda bu metriklerin pass/fail durumunu ayrı ver.

### Kabul kriteri
- Reliability tıkandığında smoke otomatik NO_GO.
- KPI contract override ile metrikler doğru parse ediliyor.

### Testler
- Yeni test: recourse funnel threshold ihlali NO_GO üretiyor.
- Yeni test: threshold parse/default merge doğru.

## 6) Çalıştırma Planı (Sıra)

1. A (reliability) + E (funnel gate) birlikte
2. B (latency hard cap)
3. C (fairness recovery)
4. D (telemetry enforcement)
5. 200 batch doğrulama
6. 1000 batch final değerlendirme
7. production smoke (prod profile)

## 7) Komut Seti (Doğrulama)

### Test
```bash
cd /Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach
pytest -q
```

### 200 müşteri hızlı kontrol
```bash
cd /Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach
TQDM_DISABLE=1 python -m credit_coach.cli.run_batch_recourse_eval \
  --n_customers 200 \
  --sample_seed 42 \
  --n_workers 5 \
  --log_every 50 \
  --base_config configs/default.yaml \
  --model_config configs/model.yaml \
  --recourse_config configs/recourse.yaml \
  --causality_config configs/causality.yaml \
  --safety_config configs/safety.yaml \
  --macro_config configs/macro.yaml
```

### 1000 müşteri final kontrol
```bash
cd /Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach
TQDM_DISABLE=1 python -m credit_coach.cli.run_batch_recourse_eval \
  --n_customers 1000 \
  --sample_seed 42 \
  --n_workers 5 \
  --log_every 100 \
  --base_config configs/default.yaml \
  --model_config configs/model.yaml \
  --recourse_config configs/recourse.yaml \
  --causality_config configs/causality.yaml \
  --safety_config configs/safety.yaml \
  --macro_config configs/macro.yaml
```

### Smoke (prod profile hedefi)
```bash
cd /Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach
python -m credit_coach.cli.run_production_smoke \
  --kpi_contract configs/kpi_contract.yaml \
  --require_telemetry_enabled
```

## 8) Sprint Exit Criteria (GO/NO_GO)

P0 sprint tamam sayılma koşulu:
- Testler geçmeli (`pytest` full green).
- 1000 batch'te latency ve fairness kontratına girilmeli.
- `denied_reliability_violation_rate` anlamlı şekilde düşmeli (<=0.40).
- Smoke prod profile `GO` dönmeli (telemetry gerçekten aktifken).

Aksi durumda sonuç `NO_GO` ve bir sonraki adım `objective/config retune` değil, doğrudan bottleneck modül düzeltmesi olur.
