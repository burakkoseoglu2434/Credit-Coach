# CREDIT COACH RECOURSE REDESIGN - FAZ UYGULAMA RAPORU

## Surum
- Tarih: `2026-03-07`
- Kapsam: Faz-1..Faz-4 uygulama + test + dogrulama
- Durum: `Tamamlandi (kod + test)`

---

## 1) Faz-1 (P0) - Gate-aligned objective + Denied-target mode + Funnel

### Yapilanlar
1. `generator.py` icinde skor fonksiyonu gate ihlali cezalarina baglandi.
   - `CI_high <= tau`
   - `reliability >= min_reliability`
   - `worst_margin >= min_worst_risk_margin`
2. `run_recourse.py` ve `run_batch_recourse_eval.py` icine `denied_target` profile secimi eklendi.
3. Batch pipeline'a zorunlu funnel ciktilari eklendi:
   - `denied_count`
   - `denied_with_any_candidate`
   - `denied_with_gate_pass_plan`
   - `denied_to_approved_lift`
4. Yeni cikti dosyalari:
   - `recourse_funnel_summary.csv`
   - `latency_outliers.csv`
   - `batch_fairness_change.csv`

### Ilgili dosyalar
- `credit-coach/src/credit_coach/recourse/generator.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/configs/recourse.yaml`

---

## 2) Faz-2 (P0/P1) - Adaptive step optimizer + Hybrid candidate pool

### Yapilanlar
1. `generator.py` icinde sabit step yerine feature-bazli adaptive step aramasi eklendi.
   - sensitivity tabanli ilk step
   - kontrollu step buyutme (`growth_factor`, `max_multiplier`, `max_attempts`)
2. `run_recourse.py` ve `run_batch_recourse_eval.py` icinde candidate pool birlestirildi:
   - `internal plans` + `dice plans`
   - ortak validator
   - ortak rerank (`choose_best_plan`)
3. `planner.py` secim mantigi gate-pass score odakli hale getirildi.

### Ilgili dosyalar
- `credit-coach/src/credit_coach/recourse/generator.py`
- `credit-coach/src/credit_coach/coaching/planner.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`

---

## 3) Faz-3 (P1) - Belirsizlik guclendirme + Fairness-regulated objective

### Yapilanlar
1. `statistical.py` icine bootstrap + conformal CI secenekleri eklendi.
   - `estimate_prediction_ci(...)`
   - `conformal_prediction_ci(...)`
2. `validator.py` icinde `uncertainty_cfg` ile `bootstrap | conformal | hybrid` secimi eklendi.
3. Fairness penalty altyapisi eklendi:
   - `build_group_advantage_penalties(...)`
   - `lookup_group_penalty(...)`
4. Objective tarafinda fairness penalty hook aktive edildi (`generator.py`).

### Ilgili dosyalar
- `credit-coach/src/credit_coach/safety/statistical.py`
- `credit-coach/src/credit_coach/safety/validator.py`
- `credit-coach/src/credit_coach/evaluation/fairness.py`
- `credit-coach/configs/safety.yaml`
- `credit-coach/configs/recourse.yaml`

---

## 4) Faz-4 (P0) - KPI contract + Release gate

### Yapilanlar
1. `run_production_smoke.py` icine `G0_BATCH_RECOURSE_KPI` gate eklendi.
2. Yeni KPI gate kontrolleri:
   - `denied_to_approved_lift >= 0.05`
   - `approval_gap_delta <= +0.01`
   - `equalized_odds_gap_delta <= +0.01`
   - `p95 <= 500 ms`
   - `p99 <= 2000 ms`
   - `error_rate <= 0.005`
3. Dokumantasyon guncellendi:
   - `README.md`
   - `docs/RELEASE_GATES.md`
   - `docs/PROD_RUNBOOK.md`

### Ilgili dosyalar
- `credit-coach/src/credit_coach/cli/run_production_smoke.py`
- `credit-coach/tests/test_production_smoke.py`
- `credit-coach/docs/RELEASE_GATES.md`
- `credit-coach/docs/PROD_RUNBOOK.md`
- `credit-coach/README.md`

---

## 5) Test Sonuclari

### Unit/Integration test
- Komut: `pytest -q`
- Sonuc: `77 passed`

### Eklenen testler
- `credit-coach/tests/test_recourse_redesign.py`
  - denied-target profile
  - fairness penalty map
  - conformal CI bounds

---

## 6) Calistirilan Gercek Pipeline Sonuclari

### Batch recourse eval (200 musteri)
- Komut:
  - `TQDM_DISABLE=1 python -m credit_coach.cli.run_batch_recourse_eval --n_customers 200 --sample_seed 42 --log_every 50`
- Run ID:
  - `20260307_021535_d24a57_fd7c08`
- Ozet (batch_summary.json):
  - `denied_count = 42`
  - `denied_with_gate_pass_plan = 39`
  - `denied_to_approved_lift = 0.9286`
  - `before_approval_rate = 0.79`
  - `after_approval_rate = 0.985`
  - `approval_rate_lift = +0.195`
  - `fairness approval gap delta = -0.1042`
  - `latency_p95_ms = 814.16`
  - `latency_p99_ms = 9735.60`
  - `error_rate = 0.0`

### Production smoke
- Komut:
  - `python -m credit_coach.cli.run_production_smoke --batch_summary_json .../batch_summary.json --batch_fairness_change_csv .../batch_fairness_change.csv`
- Run ID:
  - `20260307_021851_01a468_afaca6`
- Sonuc:
  - `NO_GO`
  - Fail gate: `G0_BATCH_RECOURSE_KPI`
  - Fail nedenleri: `latency_p95_ms`, `latency_p99_ms`

### Single recourse smoke
- Komut:
  - `python -m credit_coach.cli.run_recourse --customer_id smoke_demo --row_index 5`
- Run ID:
  - `20260307_021919_9b2a79_dabde3`
- Sonuc:
  - `plans=9 approved=9`
  - `best_source=internal`

---

## 7) Mevcut Darbogaz (Uygulama Sonrasi)
1. Lift/fairness KPI tarafi guclu, ancak latency KPI (ozellikle p99) release threshold ustunde.
2. p99 gecikmesi agirlikla DiCE satir bazli arama ve nadir outlier satirlardan geliyor.
3. Bir sonraki optimizasyon sprinti: latency odakli
   - denied-target mode icinde zaman butcesi/timeout
   - DiCE method budget (total_cfs/method fallback) dinamik kisit
   - cache ve vectorized scoring

