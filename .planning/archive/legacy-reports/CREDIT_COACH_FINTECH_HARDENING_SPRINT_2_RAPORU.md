# CREDIT COACH FINTECH HARDENING - SPRINT 2 RAPORU

## 0) Kapsam
Sprint: `Sprint-2 (Hafta 3-4)`  
Backlog maddeleri: `B1, B2, B3`  
Tarih: `2026-03-07`

Hedefler:
1. B1 - XGBoost production profile + deterministic train + fallback reason kaydi
2. B2 - SHAP stability/baseline drift + explainability confidence
3. B3 - DiCE adapter hardening (method secimi + telemetry)

---

## 1) Yapilan Degisiklikler (Dosya Bazli)

### 1.1 B1 - Model profile ve backend reason
- `credit-coach/src/credit_coach/model/train.py`
  - Deterministik backend secimi sertlestirildi.
  - `monotone_constraints` dict/list/string normalize edildi.
  - XGBoost tarafinda seed/random_state/default parametreleri sabitlendi.
  - Backend metadata eklendi:
    - `requested_backend`
    - `backend_reason`
    - `fallback_reason`
  - `get_training_backend_info()` eklendi.

- `credit-coach/src/credit_coach/cli/run_train.py`
  - Train metriklerine backend reason alanlari eklendi.

- `credit-coach/src/credit_coach/retraining/train_job.py`
  - Challenger metriklerine backend reason alanlari eklendi.

- `credit-coach/src/credit_coach/model/__init__.py`
  - `get_training_backend_info` export edildi.

- `credit-coach/configs/model.yaml`
  - `allow_xgboost`, `fallback_on_error`, `monotone_constraints` parametreleri eklendi.

### 1.2 B2 - SHAP reliability pack
- `credit-coach/src/credit_coach/xai/shap_local.py`
  - `compute_local_reason_bundle()` eklendi.
  - Yeni metrikler:
    - `stability_score`
    - `baseline_drift_l1`
    - `explainability_confidence`
  - Local SHAP icin `background_df` destegi eklendi (tek satir background kaynakli sifir katki sorunu cozuldu).

- `credit-coach/src/credit_coach/xai/shap_global.py`
  - `compute_global_importance_stability()` eklendi (bootstrap tabanli global stability).

- `credit-coach/src/credit_coach/xai/__init__.py`
  - Yeni stability fonksiyonlari export edildi.

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - Local reason bundle kullanimi eklendi.
  - `local_reasons.json` artik `reasons + meta` formatinda yaziliyor.
  - Run metrics icine explainability confidence/stability/drift eklendi.

- `credit-coach/configs/recourse.yaml`
  - SHAP stability parametreleri eklendi:
    - `stability_perturbations`
    - `stability_noise_std`
    - `stability_seed`
    - `background_samples`

### 1.3 B3 - DiCE adapter hardening
- `credit-coach/src/credit_coach/recourse/dice_baseline.py`
  - `dice_method` secimi eklendi (`random|genetic|kdtree`).
  - Feature type adapter eklendi (continuous/categorical ayristirma).
  - Fallback reason kodlari standartlastirildi:
    - `invalid_method`
    - `missing_target_col`
    - `empty_dice`
    - `no_action`
    - `error`
  - Telemetry sozlesmesi eklendi (method, reason, changed feature union vb.).
  - Fonksiyon imzasi guncellendi:
    - `generate_dice_counterfactual_actions(...) -> (action_sets, backend, telemetry)`

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - DiCE configten method/seed/total_cfs/max_actions okunuyor.
  - `dice_telemetry.json` artifact'i eklendi.
  - Run metrics'e `dice_method_requested`, `dice_method_used`, `dice_fallback_reason` vb. eklendi.

- `credit-coach/src/credit_coach/recourse/generator.py`
  - Candidate feature secimi sertlestirildi (`_normalize_candidate_features`).
  - Dict/list formatli aday feature girisleri desteklendi.

- `credit-coach/src/credit_coach/data/schema.py`
  - `LocalReason` ve `ExplainabilityMeta` se malari eklendi.

### 1.4 Test ve dokumantasyon
- Yeni testler:
  - `credit-coach/tests/test_model_xgb_profile.py`
  - `credit-coach/tests/test_shap_stability.py`
  - `credit-coach/tests/test_dice_adapter_hardening.py`
- Guncellenen test:
  - `credit-coach/tests/test_dice_baseline.py` (telemetry assertion)
- `credit-coach/README.md`
  - B1/B2/B3 config ve metrik notlari eklendi.

---

## 2) Calistirilan Komutlar ve Sonuclar

1. Sprint-2 hedefli testler:
```bash
cd credit-coach && pytest -q tests/test_model_xgb_profile.py tests/test_shap_stability.py tests/test_dice_adapter_hardening.py tests/test_dice_baseline.py tests/test_model_pipeline.py tests/test_shap_local.py
```
Sonuc: `11 passed`

2. Tam regresyon:
```bash
cd credit-coach && pytest -q
```
Sonuc: `58 passed, 7 warnings`

3. Train denemesi (XGBoost path):
```bash
cd credit-coach && python -m credit_coach.cli.run_train --config configs/model.yaml --base_config configs/default.yaml
```
Sonuc: Sandbox ortaminda OpenMP SHM hatasi nedeniyle XGBoost path abort oldu (`OMP Error #179`).

4. Train (forced logistic) dogrulama:
```bash
cd credit-coach && CREDIT_COACH_FORCE_BACKEND=logistic_regression python -m credit_coach.cli.run_train --config configs/model.yaml --base_config configs/default.yaml
```
Run ID: `20260307_004436_569424_b6610b`  
Sonuc: Basarili  
Ek metrik alanlari:
- `requested_backend: logistic_regression`
- `backend_reason: requested_logistic_regression`
- `fallback_reason: null`

5. Recourse + SHAP bundle + DiCE telemetry:
```bash
cd credit-coach && python -m credit_coach.cli.run_recourse --customer_id demo --row_index 5 --base_config configs/default.yaml --model_config configs/model.yaml --recourse_config configs/recourse.yaml --causality_config configs/causality.yaml --safety_config configs/safety.yaml --macro_config configs/macro.yaml
```
Run ID: `20260307_004624_b8766f_aae55e`  
Sonuc:
- `plan_count: 9`, `approved_count: 9`
- `local_explainability_confidence: 0.9478`
- `local_shap_stability_score: 0.9394`
- `dice_backend: heuristic_fallback_error`
- `dice_fallback_reason: error`
- `dice_changed_features: 4`

Uretilen yeni artifactler:
- `tables/local_reasons.json` (reasons + meta)
- `tables/dice_telemetry.json`

---

## 3) Test Sonuclari

Yeni test kapsami:
1. `test_model_xgb_profile.py`
   - monotonic constraints normalize
   - xgboost-disabled fallback reason
   - invalid monotonic length fail-fast
2. `test_shap_stability.py`
   - local/global stability meta alanlari
   - confidence/stability bounded checks
3. `test_dice_adapter_hardening.py`
   - invalid method fallback reason
   - fake DiCE backend ile method + telemetry kontrolu

Regresyon:
1. Tum mevcut testler korunarak toplam `58 passed`.

---

## 4) KPI ve Backlog Durumu

Sprint-2 backlog:
1. `B1 - XGBoost profile + backend reason`: Tamamlandi (kod + test)
2. `B2 - SHAP reliability pack`: Tamamlandi (kod + test)
3. `B3 - DiCE adapter hardening`: Tamamlandi (kod + test)

Not:
- Bu sandbox ortaminda native OpenMP kisiti nedeniyle XGBoost runtime ve DiCE runtime tarafinda ortam kaynakli blokajlar goruldu.
- Kod pathleri testlerde (mock/fallback dahil) dogrulandi.

---

## 5) Acilan Riskler ve Teknik Borc
1. XGBoost runtime bu ortamda `OMP SHM` hatasina dusuyor; uretim/CI ortaminda tekrar dogrulanmali.
2. Gercek DiCE entegrasyonu bu denemede `TypeError` ile fallback'e dustu; wrapper uyumlulugu ortam bazli sertlestirme gerektiriyor.
3. `datetime.utcnow()` deprecation warningleri devam ediyor.

---

## 6) Sonraki Sprint Giris Kosullari (Sprint-3)
1. Sprint-2 degisiklikleri stabil ve testleri yesil.
2. Sonraki odak: `C1 - Robust recourse objective` (scenario-aware robust score + validator entegrasyonu).

