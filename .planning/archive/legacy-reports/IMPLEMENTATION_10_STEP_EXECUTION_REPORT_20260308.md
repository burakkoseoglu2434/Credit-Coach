# CREDIT COACH - 10 Adım Uygulama ve Test Raporu (2026-03-08)

Bu rapor, backlogdaki 10 maddenin sırayla kodlanması, test edilmesi ve çıkan sonuçların kaydıdır.

## Genel Sonuç
- Durum: 10/10 adım kodlandı.
- Test durumu: `118 passed`.
- Yeni batch doğrulama run: `20260308_015943_80c790_6c8529`.
- Outcome feedback run: `20260308_020020_7f22ca_98e180`.

## Adım 1 - High-risk dönüşüm boşluğu (B1)
Yapılanlar:
- High-risk segment için ayrı profil override eklendi.
- Denied + high risk durumunda daha agresif arama profili aktive edildi.
- High-risk profil uygulanma metriği eklendi.

Kod:
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `configs/recourse.yaml`

Öne çıkan parametreler:
- `high_risk_profile.enabled`
- `topk_multiplier`, `min_topk`
- `weekly_weeks`, `weekly_max_actions`, `max_actions`
- `target_pd_margin_extra`

Test:
- `tests/test_batch_candidate_diversity.py::test_apply_high_risk_profile_overrides_denied_search`

## Adım 2 - Robust gate tıkanması (B2)
Yapılanlar:
- Segment/risk-band bazlı uncertainty profile eklendi.
- CI genişliği ve alpha dinamik olarak `risk_band + denied_mode` ile ölçekleniyor.
- Validator ve generator bu profili kullanır hale getirildi.

Kod:
- `src/credit_coach/safety/statistical.py`
- `src/credit_coach/safety/validator.py`
- `src/credit_coach/recourse/generator.py`
- `configs/safety.yaml`

Test:
- `tests/test_validator_ci.py::test_validator_applies_segment_uncertainty_profile`

## Adım 3 - Aday çeşitliliği düşük (B3)
Yapılanlar:
- Internal + DiCE + rule-based candidate havuzu kuruldu.
- Rule-based yol için deterministic heuristic aday eklendi.
- Candidate rerank tarafında novelty-aware prune eklendi.
- Diversity metrikleri eklendi:
  - `candidate_pool_diversity_index`
  - `candidate_source_entropy`
  - `best_source_rule_rate`

Kod:
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `configs/recourse.yaml`

Test:
- `tests/test_batch_candidate_diversity.py::test_prune_candidate_pool_with_novelty_increases_diversity`

## Adım 4 - Fairness kapsamı dar (B4)
Yapılanlar:
- Multi-segment fairness hesaplayıcı eklendi (tek grup + kesişimli gruplar).
- Batch eval tarafına multi-segment fairness karşılaştırma tablosu eklendi.
- Fairness CLI tarafına da multi-segment rapor eklendi.

Kod:
- `src/credit_coach/evaluation/fairness.py`
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `src/credit_coach/cli/run_fairness.py`

Yeni çıktı:
- `batch_fairness_multi_segment.csv`
- `fairness_multi_segment_report.csv`

Test:
- `tests/test_multi_segment_fairness.py`

## Adım 5 - Model evaluation metodolojisi (B5)
Yapılanlar:
- Kalibrasyon test setinden ayrıldı.
- Eğitim hattı `train_core / calibration / test` protokolüne geçti.
- Conformal calibration kaynağı `calibration_split` oldu.
- Split protocol artifact eklendi.

Kod:
- `src/credit_coach/data/split.py`
- `src/credit_coach/cli/run_train.py`
- `configs/default.yaml`
- `configs/model.yaml`

Yeni çıktı:
- `split_protocol_report.json`

Test:
- `tests/test_data_pipeline.py::test_split_train_calibration_contract`

## Adım 6 - Offline KPI vs gerçek sonuç boşluğu (B6)
Yapılanlar:
- DB’ye delayed outcome tablosu eklendi: `decision_outcomes`.
- Outcome upsert + policy delta özet fonksiyonları eklendi.
- Outcome feedback CLI eklendi.

Kod:
- `src/credit_coach/storage/models.py`
- `src/credit_coach/storage/repository.py`
- `src/credit_coach/data/schema.py`
- `src/credit_coach/cli/run_outcome_feedback.py`

Test:
- `tests/test_outcome_feedback.py`

Çıktı (örnek run):
- `approval_rate_delta = 0.5`
- `default_rate_90d_delta = -1.0`
- `avg_margin_90d_delta = 140.0`

## Adım 7 - Telemetry prod’da zorunlu değil (B7)
Yapılanlar:
- KPI contract default’unda telemetry zorunlu hale getirildi.
- Smoke gate’e telemetry başarı oranı ve ingest lag kontrolleri eklendi.
- Monitoring çıktılarına telemetry success rate/lag alanları eklendi.

Kod:
- `src/credit_coach/ops/kpi_contract.py`
- `src/credit_coach/cli/run_production_smoke.py`
- `src/credit_coach/cli/run_monitoring.py`
- `configs/kpi_contract.yaml`

Test:
- `tests/test_kpi_contract.py`
- `tests/test_production_smoke.py`

## Adım 8 - Tail latency duyarlılığı (B8)
Yapılanlar:
- Candidate pool boş kaldığında deterministic fallback plan eklendi.
- Timeout/fallback oran metrikleri eklendi.

Kod:
- `src/credit_coach/cli/run_batch_recourse_eval.py`

Yeni metrikler:
- `timeout_or_fallback_rate`
- `best_source_fallback_rate`
- `fallback_triggered`, `fallback_reason`

Test:
- Full suite regression + batch run doğrulaması.

## Adım 9 - Regülasyon seviyesinde açıklama (B9)
Yapılanlar:
- Adverse action payload üretimi eklendi:
  - principal reason codes
  - reason details
  - remediation hint
  - specificity validation
- Policy engine reject durumunda adverse action payload döndürür hale getirildi.

Kod:
- `src/credit_coach/coaching/messaging.py`
- `src/credit_coach/policy/engine.py`

Test:
- `tests/test_messaging.py`
- `tests/test_policy_engine.py`

## Adım 10 - Governance hardening (B10)
Yapılanlar:
- Governance değerlendirmesi genişletildi:
  - required approvers
  - required artifact hashes
  - rollback drill koşulu
- Retrain pipeline bu workflow’u hesaplayıp decision çıktısına yazar hale getirildi.
- Governance raporuna compliance alanları eklendi.

Kod:
- `src/credit_coach/retraining/governance.py`
- `src/credit_coach/cli/run_retrain.py`
- `src/credit_coach/cli/run_governance_report.py`
- `configs/governance.yaml`

Test:
- `tests/test_governance_workflow.py`

## Test Çıktısı
Çalıştırılan ana komut:
- `pytest -q`

Sonuç:
- `118 passed in 20.20s`

## Batch Çıktısı (Yeni Kod)
Komut:
- `python -m credit_coach.cli.run_batch_recourse_eval --n_customers 120 --sample_seed 42 --n_workers 5 ...`

Run:
- `artifacts/runs/20260308_015943_80c790_6c8529`

Öne çıkan metrikler:
- `denied_to_approved_lift = 0.0417`
- `denied_high_risk_lift = 0.0`
- `dice_success_rate = 0.20`
- `best_source_rule_rate = 0.1417`
- `candidate_pool_diversity_index = 0.1317`
- `candidate_source_entropy = 0.1764`
- `high_risk_profile_applied_rate = 0.1417`
- `timeout_or_fallback_rate = 0.0`

## Notlar
- `run_retrain` CLI çalıştırması bu sandbox ortamında `OMP SHM` hatası verdi.
- Governance değişiklikleri unit testlerle doğrulandı; fonksiyonel kod aktif.
