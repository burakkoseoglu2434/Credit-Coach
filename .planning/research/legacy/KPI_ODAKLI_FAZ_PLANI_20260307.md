# CREDIT COACH - KPI ODAKLI FAZ PLANI (2026-03-07)

## 1) Amac ve Kapsam
Bu planin amaci, projeyi "teknik olarak calisiyor" seviyesinden "fintech urun KPI'larini surekli gecen" seviyesine tasimaktir.

Kritik hedef:
- `denied_to_approved_lift` metrigini kalici sekilde `>= 0.05` yapmak
- bunu yaparken fairness, latency, error ve governance kapilarini bozmamak

Bu dokuman sadece plani icerir. Kod uygulamasi bir sonraki adimda faz faz yapilacaktir.

## 2) Baseline (Bugun Nerede?)
Referans NO_GO:
- Smoke run: `artifacts/runs/20260307_144607_05d549_076a80/tables/production_smoke_report.csv`
- Batch run: `artifacts/runs/20260307_144459_df1dd8_3256ab/tables/batch_summary.json`

Mevcut durum:
- `denied_to_approved_lift = 0.008438818565400843` (FAIL, hedef `>= 0.05`)
- `approval_gap_delta = -0.0004760721973835` (PASS)
- `equalized_odds_gap_delta = -0.0112359550561798` (PASS)
- `latency_p95_ms = 132.74480030231643` (PASS)
- `latency_p99_ms = 305.71123290515965` (PASS)
- `error_rate = 0.0` (PASS)
- `denied_not_approved_top_root_cause = reliability_gate`
- `denied_not_approved_top_root_cause_share = 0.9957446808510638`

Sonuc:
- Problem ana olarak "denied musteri icin gate-pass plan uretememe"
- Ozellikle `reliability_gate` darbogazi baskin

## 3) KPI Contract (Olculmesi Zorunlu Metrikler)

### 3.1 L0 - Urun Etkinligi (Primary Business KPI)
1. `denied_to_approved_lift`
- Formula: `denied_with_gate_pass_plan / denied_count`
- Kaynak: `recourse_funnel_summary.csv`, `batch_summary.json`
- Hedef: `>= 0.05` (pilot)

2. `denied_high_risk_lift`
- Formula: `high_risk band gate-pass / high_risk denied`
- Kaynak: `batch_summary.json`, `denied_lift_by_income_risk.csv`
- Hedef: `>= 0.02` (asama 1), `>= 0.04` (asama 2)

3. `denied_with_any_candidate_rate`
- Formula: `denied_with_any_candidate / denied_count`
- Kaynak: `recourse_funnel_summary.csv`
- Hedef: `>= 0.95`

### 3.2 L1 - Guvenlik/Fairness KPI
1. `approval_gap_delta <= +0.01`
2. `equalized_odds_gap_delta <= +0.01`
3. `recourse_success_gap <= 0.10`
4. `recourse_cost_gap <= 500`
5. `high_stress_fairness_gap <= 0.10`

Kaynaklar:
- `batch_fairness_change.csv`
- `batch_recourse_fairness.csv`
- `fairness_report.csv`
- `fairness_stress_matrix.csv`

### 3.3 L2 - Operasyonel KPI
1. `latency_p95_ms <= 500`
2. `latency_p99_ms <= 2000`
3. `error_rate <= 0.005`
4. `latency_outlier_count` trendi azalan

Kaynaklar:
- `batch_summary.json`
- `latency_outliers.csv`

### 3.4 L3 - Model/Robustness KPI
1. `last_k_validity >= 0.85`
2. `last_k_safe_rate >= 0.60`
3. `last_k_avg_risk_margin >= 0.00`
4. `avg_reliability >= 0.70`

Kaynaklar:
- `benchmark_lastk_summary.csv`
- `shock_reliability.csv`
- `monitoring_summary.csv`

## 4) Faz Bazli Uygulama Plani

### Faz 0 - Baseline Freeze ve KPI Iskeleti (P0)
Amac:
- Deneyleri karsilastirilabilir hale getirmek
- KPI hesaplamasini tek "contract" dosyasina baglamak

Kod degisim alani:
- `configs/kpi_contract.yaml` (yeni)
- `src/credit_coach/ops/kpi_contract.py` (yeni)
- `src/credit_coach/cli/run_production_smoke.py` (contract'tan threshold okuma)
- `src/credit_coach/ops/telemetry.py` (KPI metric setini standardize etme)

Test:
- `tests/test_kpi_contract.py` (yeni)
- mevcut smoke/monitoring testleri

Cikis kriteri:
- KPI threshold'lar tek noktadan yonetiliyor olmasi
- smoke ve telemetry outputunda KPI alanlari tutarli olmasi

### Faz 1 - Denied Funnel Diagnostik Derinlestirme (P0)
Amac:
- Lift neden cikmiyor sorusunu segment ve root-cause seviyesinde netlestirmek

Kod degisim alani:
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `src/credit_coach/evaluation/fairness.py`

Eklenecek metrikler:
- `denied_reliability_violation_rate`
- `denied_ci_violation_rate`
- `denied_worst_margin_violation_rate`
- `denied_internal_vs_dice_gate_pass_share`
- `denied_lift_by_risk_band`
- `denied_lift_by_income_band`

Yeni output:
- `denied_gate_violation_breakdown.csv`
- `denied_candidate_source_breakdown.csv`

Test:
- `tests/test_recourse_funnel_kpis.py` (yeni)

Cikis kriteri:
- Root-cause analizi tek dosyada gorulebilir olmasi
- KPI raporu denied segmentlerde tutarli olmasi

### Faz 2 - Denied Objective Tuning (P0)
Amac:
- Optimizer'i gate-pass hedefi ile tam hizalamak

Kod degisim alani:
- `src/credit_coach/recourse/generator.py`
- `src/credit_coach/coaching/planner.py`
- `configs/recourse.yaml` (`robust.denied_objective`)

Teknik adimlar:
1. `ci`, `reliability`, `worst_margin` violation agirliklarini risk banda gore ayri tune et
2. denied musteri icin secim sirasini "gate-violation minimization first" yap
3. cost/sparsity sadece ikinci sirada kalsin

Test:
- `tests/test_planner_denied_objective.py`
- `tests/test_robust_recourse.py`

Cikis kriteri:
- 200 customer dry-run: `denied_to_approved_lift >= 0.03`
- reliability kaynakli red payinda anlamli dusus

### Faz 3 - Segment-Aware Feasibility Tuning (P0)
Amac:
- Uygulanabilirlik sinirlarini segment bazli optimize ederek lift artirmak

Kod degisim alani:
- `src/credit_coach/recourse/feasibility.py`
- `configs/recourse.yaml` (`segment_caps`)
- `configs/recourse_feasibility.yaml`

Teknik adimlar:
1. income/risk banda gore cap multiplier grid search
2. global hard cap ihlalini mutlak engelle
3. q1 ve high-risk icin "gercekci aksiyon seti" odakli ayar

Test:
- `tests/test_recourse_feasibility.py`
- yeni: `tests/test_segment_caps_grid_guardrail.py`

Cikis kriteri:
- 200 customer dry-run: `denied_to_approved_lift >= 0.04`
- fairness delta gate bozulmamasi

### Faz 4 - Weekly Multi-Step Planner Stabilizasyonu (P1)
Amac:
- Tek adimda gecilemeyen denied musteriler icin haftalik staged gecis

Kod degisim alani:
- `src/credit_coach/recourse/generator.py` (`weekly_optimizer`)
- `src/credit_coach/coaching/loop.py`
- `configs/recourse.yaml` (`weekly_optimizer` budget)

Teknik adimlar:
1. week-by-week beam pruning
2. early-stop: gate-pass yakalaninca dur
3. worst-case latency'yi kontrol etmek icin time budget enforcement

Test:
- `tests/test_recourse_redesign.py`
- `tests/test_sequential_recourse.py`

Cikis kriteri:
- 1000 batch: `latency_p95 <= 500`, `latency_p99 <= 2000` korunurken lift artisi

### Faz 5 - Candidate Source Ensemble (Internal + DiCE) (P1)
Amac:
- Aday havuzunu genisletip gate-pass sansini arttirmak

Kod degisim alani:
- `src/credit_coach/recourse/dice_baseline.py`
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `src/credit_coach/coaching/planner.py`

Teknik adimlar:
1. denied segmentte DiCE kotasini risk band'a gore dinamik belirle
2. internal + dice adaylarini tek havuzda rerank et
3. "internal approved varsa dice skip" kuralini sadece non-denied icin kullan

Test:
- `tests/test_dice_baseline.py`
- `tests/test_dice_adapter_hardening.py`

Cikis kriteri:
- `denied_internal_vs_dice_gate_pass_share` dengesi iyilesmesi
- high-risk denied segmentte sifir-lift durumunun kirilmasi

### Faz 6 - Uncertainty ve Calibration Iyilestirmesi (P1)
Amac:
- reliability gate'i daha bilgi tasiyan bir belirsizlik modeli ile guclendirmek

Kod degisim alani:
- `src/credit_coach/safety/statistical.py`
- `src/credit_coach/model/calibrate.py`
- `configs/safety.yaml`

Teknik adimlar:
1. bootstrap + conformal hibrit skor
2. calibration drift kontrolu
3. CI width ve gate failure iliskisinin raporlanmasi

Test:
- `tests/test_conformal_calibration.py`
- `tests/test_validator_ci.py`

Cikis kriteri:
- `denied_reliability_violation_rate` anlamli dusus
- model/fairness KPI bozulmamasi

### Faz 7 - GO/NO_GO Otomasyonu ve KPI Dashboard (P0)
Amac:
- Uretim kararini manuel yorumdan cikartip otomatik policy'ye baglamak

Kod degisim alani:
- `src/credit_coach/cli/run_production_smoke.py`
- `src/credit_coach/ops/telemetry.py`
- `src/credit_coach/cli/run_monitoring.py`

Teknik adimlar:
1. `kpi_snapshot.json` standard output
2. `production_smoke_report.json` icinde KPI trend karsilastirmasi (onceki run'a gore)
3. Prometheus/OTLP etiketlerinde run_id + model_version + config_hash

Test:
- `tests/test_production_smoke.py`
- `tests/test_telemetry_export.py`

Cikis kriteri:
- tek komutla release karari + KPI kanitlari uretilmesi

## 5) Deney Matrisi (Uygulama Sirasi)
Her faz sonrasi ayni sekans calisacak:

1. `pytest -q`
2. `python -m credit_coach.cli.run_batch_recourse_eval --n_customers 200 --sample_seed 42 --log_every 50 --n_workers 5 --base_config configs/default.yaml --model_config configs/model.yaml --recourse_config configs/recourse.yaml --causality_config configs/causality.yaml --safety_config configs/safety.yaml --macro_config configs/macro.yaml`
3. KPI check (200)
4. `python -m credit_coach.cli.run_batch_recourse_eval --n_customers 1000 --sample_seed 42 --log_every 100 --n_workers 5 --base_config configs/default.yaml --model_config configs/model.yaml --recourse_config configs/recourse.yaml --causality_config configs/causality.yaml --safety_config configs/safety.yaml --macro_config configs/macro.yaml`
5. `python -m credit_coach.cli.run_benchmark --model_config configs/model.yaml --window_size 3 --window_step 1 --last_k_windows 3`
6. `python -m credit_coach.cli.run_fairness --base_config configs/default.yaml --model_config configs/model.yaml --macro_config configs/macro.yaml --group_feature home_ownership`
7. `python -m credit_coach.cli.run_monitoring --base_config configs/default.yaml --monitoring_config configs/monitoring.yaml`
8. `python -m credit_coach.cli.run_production_smoke`

## 6) Fazlar Arasi Exit Gates

Faz ilerleme kurali:
- Bir fazdan digerine gecis icin:
  - Yeni eklenen testler PASS
  - Mevcut testlerde regresyon yok
  - L1/L2 KPI'larda FAIL olusturmadan L0 KPI iyilesmis olmali

Final GO:
- `denied_to_approved_lift >= 0.05`
- fairness/latency/error kapilari PASS
- benchmark + robustness + audit kapilari PASS

## 7) Riskler ve Rollback Kurali
Riskler:
- lift artarken fairness bozulmasi
- weekly optimizer nedeniyle tail latency patlamasi
- asiri cap gevsetme ile gercek disi planlar

Rollback:
- herhangi bir adimda `approval_gap_delta` veya `equalized_odds_gap_delta` limit disina cikarsa
- veya `latency_p99_ms > 2000` olursa
- son stabil `config_snapshot.yaml` profiline donulecek

## 8) Bir Sonraki Uygulama Adimi
Kodlamaya su sirayla gececegiz:
1. Faz 0 (KPI contract altyapisi)
2. Faz 1 (denied funnel diagnostiklerini genisletme)
3. Faz 2 (denied objective tuning)
4. Faz 3 (segment cap tuning)
5. Faz 4-5-6 (planner + candidate + uncertainty)
6. Faz 7 (release otomasyonu)

Bu siralama ile once olcum altyapisi ve darbogaz gorunurlugu netlesecek, sonra lift artiran degisiklikler kontrollu sekilde eklenecek.
