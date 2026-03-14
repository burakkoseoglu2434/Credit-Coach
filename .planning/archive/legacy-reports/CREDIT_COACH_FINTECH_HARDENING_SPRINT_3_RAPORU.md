# CREDIT COACH FINTECH HARDENING - SPRINT 3 RAPORU

## 0) Kapsam
Sprint: `Sprint-3 (Hafta 5-6)`  
Backlog maddesi: `C1 - Robust recourse objective`  
Tarih: `2026-03-07`

Hedef:
1. Plan uretiminde scenario-aware robust skor kullanmak.
2. Validator tarafinda reliability/worst-margin gate eklemek.
3. Robust metrikleri artifact ve run metrics ciktilarina yazmak.

---

## 1) Yapilan Degisiklikler (Dosya Bazli)

### 1.1 Robust skorleme ve macro reliability
- `credit-coach/src/credit_coach/macro/reliability.py`
  - `evaluate_reliability_from_pd` genisletildi:
    - `cvar_stressed_pd`
    - `avg_stressed_tau`
    - `robust_margin_worst`
    - `robust_margin_cvar`
  - `compute_robust_anchor_pd()` eklendi (`cvar` / `worst_case`).

- `credit-coach/src/credit_coach/macro/__init__.py`
  - `compute_robust_anchor_pd` export edildi.

### 1.2 Recourse generator entegrasyonu
- `credit-coach/src/credit_coach/recourse/generator.py`
  - Robust objective skor fonksiyonu eklendi.
  - `robust_cfg` (`objective`, `cvar_quantile`, `weights`) destegi eklendi.
  - Plan alanlari dolduruluyor:
    - `reliability`
    - `robust_score`
    - `robust_margin`
    - `robust_anchor_pd`
    - `robust_method`
    - `robust_worst_risk_margin`
  - `score` artik robust mod aciksa robust objective'e gore belirleniyor.

### 1.3 Validator robust gate
- `credit-coach/src/credit_coach/safety/validator.py`
  - Yeni opsiyonel parametreler:
    - `scenarios`
    - `threshold_shift_per_msi_unit`
    - `robust_objective`
    - `robust_cvar_quantile`
    - `min_reliability`
    - `min_worst_risk_margin`
  - CI kuralina ek olarak reliability/worst-margin gate eklendi.

### 1.4 CLI ve config entegrasyonu
- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `recourse.yaml` altindan robust config okunuyor.
  - `macro.yaml` shock_scenarios ve threshold shift validator/generator'a aktariliyor.
  - `plans.csv` satirina robust kolonlar eklendi:
    - `reliability`
    - `robust_score`
    - `robust_margin`
    - `robust_anchor_pd`
    - `robust_method`
    - `robust_worst_risk_margin`
  - Run metrics'e robust ozetler eklendi:
    - `robust_objective`, `robust_cvar_quantile`
    - `avg_reliability`, `avg_robust_score`, `min_robust_margin`

- `credit-coach/configs/recourse.yaml`
  - Yeni `robust` bolumu eklendi:
    - `enabled`
    - `objective`
    - `cvar_quantile`
    - `min_reliability`
    - `min_worst_risk_margin`
    - `weights`

### 1.5 Sema ve dokumantasyon
- `credit-coach/src/credit_coach/data/schema.py`
  - `PlanRecord` icine robust alanlar eklendi.

- `credit-coach/README.md`
  - C1 robust config ve cikti kolon notlari eklendi.

---

## 2) Test Gelistirmeleri

Yeni test:
- `credit-coach/tests/test_robust_recourse.py`
  1. Generator robust score uretimini dogrular.
  2. Validator reliability gate davranisini dogrular.

Guncellenen test:
- `credit-coach/tests/test_validator_ci.py`
  - `reliability` alaninin dolduruldugu assert edildi.

---

## 3) Calistirilan Komutlar ve Sonuclar

1. Hedefli testler:
```bash
cd credit-coach && pytest -q tests/test_robust_recourse.py tests/test_validator_ci.py tests/test_shock_reliability.py tests/test_model_pipeline.py tests/test_dice_baseline.py
```
Sonuc: `8 passed`

2. Tam regresyon:
```bash
cd credit-coach && pytest -q
```
Sonuc: `60 passed, 9 warnings`

3. Uctan uca recourse:
```bash
cd credit-coach && python -m credit_coach.cli.run_recourse --customer_id demo --row_index 5 --base_config configs/default.yaml --model_config configs/model.yaml --recourse_config configs/recourse.yaml --causality_config configs/causality.yaml --safety_config configs/safety.yaml --macro_config configs/macro.yaml
```
Run ID: `20260307_005324_392203_68a860`  
Sonuc:
- `plan_count: 9`
- `approved_count: 9`
- `robust_objective: cvar`
- `avg_reliability: 1.0`
- `avg_robust_score: 16.6970`
- `min_robust_margin: 0.3266`

Ornek plans.csv kolonlari:
- `robust_score`
- `robust_margin`
- `robust_anchor_pd`
- `robust_method`
- `robust_worst_risk_margin`

---

## 4) Backlog Durumu
Sprint-3 backlog:
1. `C1 - Robust recourse objective`: Tamamlandi (kod + test + run output)

Sprint gate:
1. Robust skor ve robust gate plan akisina entegre edildi.
2. Testler yesil (`60 passed`).

---

## 5) Acilan Riskler ve Teknik Borc
1. Bu ortamda DiCE tarafinda runtime fallback (`heuristic_fallback_error`) devam ediyor.
2. `datetime.utcnow()` deprecation warningleri devam ediyor.
3. Robust skor su an config-weight tabanli heuristic; bir sonraki adimda resmi backtesting pencerelerinde kalibrasyon gerekecek.

---

## 6) Sonraki Sprint Giris Kosullari (Sprint-4)
1. C1 tamamlandi.
2. Sonraki odak: `C2 - Sequential recourse planner` (haftalik multi-step transition + dinamik replan tetikleyicileri).

