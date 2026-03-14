# Credit Coach - 3 Kritik Nokta Icin Derin Arastirma Temelli Uygulama Plani (2026-03-09)

## 0) Kapsam ve Hedef
Bu plan, asagidaki 3 teknik darbozagi kapatmak icin arastirma + uygulama yol haritasidir:
1. Fairness metriklerinin seed-bazli stabil olmamasi
2. Aday plan cesitliliginin dusuk kalmasi (DiCE ve diger uretec etkisi)
3. Offline KPI ile gercek is etkisi (default/NPL/margin) arasinda kapali dongu eksigi

Bu dosya, kodlama fazina gecince backlog ve acceptance gate olarak kullanilacaktir.

---

## 1) Mevcut Baseline (Son 1000x5)
Kaynak run: `artifacts/runs/20260309_185511_25dce1_5dc05b`

- pass_count: `2/5`
- mean_denied_to_approved_lift: `0.1463` (hedef geciliyor)
- mean_denied_high_risk_lift: `0.1578` (hedef geciliyor)
- mean_denied_reliability_violation_rate: `0.1849` (hedef geciliyor)
- mean_sync_latency_p95/p99: `450/450` (hedef geciliyor)
- sorun: fairness checkleri seed bazinda kiriliyor (`equalized_odds_gap_delta`, `fairness_gap_after`, `high_stress_fairness_gap_after`, bazi runlarda `recourse_success_gap`)

Yani ana blokaj artik lift/latency degil, fairness + stabilite + gercek dunya etki olcumu.

---

## 2) Arastirma Sentezi (Neden Bu Plan?)

### 2.1 Fairness ve recourse
- Fairlearn `ThresholdOptimizer` ve postprocessing yaklasimi, grup-bazli hata orani esitligi icin pratik bir cati sunuyor.
- `MetricFrame` intersecting-groups analizi, tek feature fairness yerine kesisimli segment analizi gerektigini netlestiriyor.
- Hardt et al. (Equality of Opportunity), classifier cikisina adil postprocess eklenebilecegini gosteriyor.
- Bell et al. (2024), recourse fairness'inde effort/time boyutunun zorunlu oldugunu vurguluyor.

### 2.2 Candidate diversity / recourse quality
- DiCE (FAccT 2020), diversity + feasibility trade-off'unu explicit optimize ediyor.
- FACE (AIES 2020), feasible path (sadece tek adim degil yol) gerekliligini ortaya koyuyor.
- AReS (NeurIPS 2020), global recourse ozetleri ile populasyon seviyesinde model bias ve recourse kalitesini olcuyor.
- CARLA, farkli recourse algoritmalarini ayni benchmarkta karsilastirmak icin pratik bir benchmark altyapisi sunuyor.
- Ustun actionable-recourse paketi, linear-surrogate dogrulama ve feasibility audit icin guclu bir baseline sagliyor.

### 2.3 Offline -> online etki olcumu
- OBP (Open Bandit Dataset and Pipeline), off-policy evaluation (IPS/DR vb.) icin uretimsel bir metodoloji sunuyor.
- MAPIE risk-control/conformal yaklasimlari, finite sample belirsizliginde threshold secimini daha guvenli yapiyor.
- SR 11-7 ve BCBS 239, model governance + veri raporlama izlenebilirligi icin bankacilik standardini netlestiriyor.
- CFPB guidance (2022/2023), adverse-action nedenlerinin spesifik ve dogru olmasini zorunlu hale getiriyor.

---

## 3) Uygulama Mimarisine Gore 3-Pillar Plan

## Pillar A - Fairness'i Seed-Robust Hale Getirme
Amaç: 1000x5'te fairness gate'in deterministic ve stabil PASS vermesi.

### A1) Fairness olcumunu belirsizlik-duyarli yap
- Ne eklenecek:
  - `bootstrap CI` ve `Wilson/Beta-Binomial shrinkage` ile kucuk segmentlerde asiri oynakligi bastir.
  - `min_segment_n` altinda metrici "insufficient_data" olarak isaretle; hard-fail yerine weightli fail skoruna cevir.
- Kod:
  - `src/credit_coach/evaluation/fairness.py`
  - `src/credit_coach/cli/run_batch_recourse_eval.py`
- KPI gate:
  - `fairness_metric_nan_rate = 0`
  - `seedler arasi fairness std <= 0.015`

### A2) Fairness'i planner objective'ine native gom
- Ne eklenecek:
  - Sadece postprocess demotion degil, secim aninda Lagrangian fairness ceza terimi.
  - Segment-bazli quota: `income_band x risk_band` seviyesinde recourse basari farkina cap.
- Kod:
  - `src/credit_coach/coaching/planner.py`
  - `src/credit_coach/recourse/generator.py`
  - `configs/experiments/recourse_phaseb_hybrid_v2.yaml`
- KPI gate:
  - `max_recourse_success_gap <= 0.10`
  - `max_high_stress_fairness_gap <= 0.10`
  - `5 seedde en az 4 PASS`

### A3) Fairness guard v2 (global demotion yerine segment-aware)
- Ne eklenecek:
  - Demotion adayi seciminde `segment deficit score` kullan.
  - Lift floor ihlali olmadan fairness iyilesmesini max et.
  - "no_improving_candidate" icin fallback: segment bazli micro-demotion + alternative source promotion.
- Kod:
  - `run_batch_recourse_eval.py` (`_apply_label_aware_fairness_guard`)
- KPI gate:
  - `fairness_guard_stop_reason=no_improving_candidate` oraninda belirgin dusus

### A4) Seed-robust tuning harness
- Ne eklenecek:
  - fairness weight, quota, min_improvement parametreleri icin otomatik grid/BO tarama.
  - objective: worst-seed fairness score minimizasyonu (mean degil min-max).
- Kod:
  - yeni CLI: `run_fairness_seed_robust_tuning.py`
- KPI gate:
  - `1000x5 -> 5/5 PASS`

---

## Pillar B - Candidate Diversity ve DiCE Etkinligini Arttirma
Amaç: tek kaynaga sikismayi kirip, gate-pass olasiligini cesitli adaylarla arttirmak.

### B1) DiCE hardening (calisir hale getirme)
- Ne eklenecek:
  - method cascade: `random -> genetic -> kdtree` + timeout/budget aware fallback.
  - DiCE telemetry reason taxonomy: `empty_cf`, `feature_mismatch`, `backend_error`, `timeout`.
  - continuous/categorical metadata dogrulama ve train/query schema strict check.
- Kod:
  - `src/credit_coach/recourse/dice_baseline.py`
  - `run_batch_recourse_eval.py` (diagnostics tablolari)
- KPI gate:
  - `dice_success_rate >= 0.15`
  - `dice_backend_dice_count > 0`

### B2) Multi-generator candidate pool + novelty rerank
- Ne eklenecek:
  - kaynaklar: `internal + dice + rule(last resort)`
  - MMR/DPP-benzeri rerank: `gate_pass_prob - cost + novelty`
  - ayni feature setini tekrar eden adaylara diversity cezasi.
- Kod:
  - `coaching/planner.py`
  - `recourse/generator.py`
  - `configs/experiments/recourse_phaseb_hybrid_v2.yaml` (`novelty_weight` vb.)
- KPI gate:
  - `candidate_source_entropy >= 0.60`
  - denied pop icinde `>=2 source` aday oraninda artis

### B3) Feasible path ve longitudinal plausibility
- Ne eklenecek:
  - FACE benzeri "path feasibility" skoru: tek sıcrama yerine ara adimlar.
  - longitudinal fark metrikleri (Asemota/Hooker) ile "gercekte degisebilirlik" puani.
- Kod:
  - yeni modul: `src/credit_coach/recourse/plausibility.py`
  - entegrasyon: `generator.py`, `feasibility.py`
- KPI gate:
  - `candidate_pd_delta>0` high-risk denied oraninda artis
  - `implausible_action_rate` dususu

### B4) Recourse benchmark harness (CARLA-style)
- Ne eklenecek:
  - ayni dataset/model uzerinde method karsilastirma:
    - validity, proximity, sparsity, diversity, feasibility, fairness gap
- Kod:
  - yeni CLI: `run_recourse_benchmark_matrix.py`
- KPI gate:
  - secilen "champion recourse" methodunun en az 3 ana metrige ustunlugu

---

## Pillar C - Offline KPI'dan Gercek Is KPI'ina Gecis
Amaç: "modeli gecirdi" metriginden "gercek default/margin etkisi" metrigine gecmek.

### C1) Policy logging kontrati (A/B + OPE hazir)
- Ne eklenecek:
  - her karar icin: `policy_arm`, `propensity`, `candidate_set_id`, `reason_codes`, `accepted_plan_flag`, `timestamp`.
  - adverse action reason code sozlugu.
- Kod:
  - `src/credit_coach/data/schema.py`
  - `src/credit_coach/storage/models.py`
  - `src/credit_coach/storage/repository.py`
- KPI gate:
  - `decision_log_completeness >= 99.5%`

### C2) Controlled experimentation (online AB)
- Ne eklenecek:
  - randomization unit ve guardrail stop rules.
  - CUPED/variance reduction opsiyonlari (opsiyonel) + confidence interval raporu.
- Kod:
  - `src/credit_coach/cli/run_high_risk_ab.py`
  - yeni rapor: `ab_significance_report.json`
- KPI gate:
  - treatment uplift istatistiksel anlamli + fairness guardrail PASS

### C3) OPE (IPS/DR) ve delayed outcome pipeline
- Ne eklenecek:
  - 30/60/90 gun outcome ingestion + DR tahminleri.
  - `approval_rate_delta`, `default_rate_delta`, `margin_delta` icin CI.
- Kod:
  - `src/credit_coach/cli/run_outcome_feedback.py`
  - yeni modul: `src/credit_coach/evaluation/offpolicy.py`
- KPI gate:
  - sadece offline lift degil, `default_rate_90d_delta <= 0` dogrulama

### C4) Governance ve audit readiness
- Ne eklenecek:
  - model card + recourse policy card + release checklist.
  - SR11-7 model inventory/validation kayitlari.
- Kod/dokuman:
  - `docs/` altina standart rapor templateleri
- KPI gate:
  - release icin zorunlu dokuman ve telemetry evidence tamam

---

## 4) Fazlama ve Kodlama Sirasi (P0 -> P2)

### Faz-1 (P0, 1-2 sprint)
- A1, A2, A3
- B1
- C1
Beklenen cikti:
- fairness seed stabilitesinde ilk buyuk iyilesme
- DiCE sifirdan cikis

### Faz-2 (P0/P1, 1-2 sprint)
- B2, B3
- A4
- C2
Beklenen cikti:
- 1000x5'te 5/5 PASS'e yakinlasma
- candidate entropy ve source diversity artis

### Faz-3 (P1/P2, 1-2 sprint)
- B4
- C3, C4
Beklenen cikti:
- online etki olcumu + governance readiness

---

## 5) Net KPI Contract (Bu plan sonunda hedef)
1. `denied_to_approved_lift >= 0.09`
2. `denied_high_risk_lift >= 0.03`
3. `denied_reliability_violation_rate <= 0.40`
4. `sync_latency_p95 <= 500ms`, `p99 <= 2000ms`
5. `equalized_odds_gap_delta <= 0.01`
6. `fairness_gap_after <= 0.10`
7. `high_stress_fairness_gap_after <= 0.10`
8. `recourse_success_gap <= 0.10`
9. `candidate_source_entropy >= 0.60`
10. `dice_success_rate >= 0.15`
11. `1000x5 seed PASS = 5/5`
12. Online: `default_rate_90d_delta <= 0` + CI

---

## 6) Kod Degisikligi Haritasi (Oncelikli Dosyalar)
- Fairness:
  - `src/credit_coach/evaluation/fairness.py`
  - `src/credit_coach/coaching/planner.py`
  - `src/credit_coach/cli/run_batch_recourse_eval.py`
  - `configs/experiments/recourse_phaseb_hybrid_v2.yaml`
- Diversity/DiCE:
  - `src/credit_coach/recourse/dice_baseline.py`
  - `src/credit_coach/recourse/generator.py`
  - `src/credit_coach/recourse/feasibility.py`
  - `src/credit_coach/recourse/action_space.py`
- Offline->online:
  - `src/credit_coach/data/schema.py`
  - `src/credit_coach/storage/models.py`
  - `src/credit_coach/storage/repository.py`
  - `src/credit_coach/cli/run_high_risk_ab.py`
  - `src/credit_coach/cli/run_outcome_feedback.py`
  - `src/credit_coach/ops/kpi_contract.py`
  - `configs/kpi_contract.yaml`

---

## 6.1) Ek Odak - Cok Katmanli Musteri Plani (Trajectory Recourse)
Bu odak, \"tek seferde gecir\" yerine \"hafta/ay bazli ilerleyerek gecir\" yaklasimini urune tasir.

Neden:
- Mevcut motor haftalik optimizasyonu icte kullaniyor, ancak ciktiyi tek plan ozetine sikistiriyor.
- Low-score segmentte tek adimda gate-pass beklemek gercekci degil; ara kilometre taslari lazim.

### T1) Plan veri modelini fazli hale getir
- Ne eklenecek:
  - `PlanAction` ve/veya yeni `TrajectoryStep` icin:
    - `phase_id` (stabilize/build/optimize),
    - `week_start`, `week_end`,
    - `prerequisites`,
    - `expected_pd_delta`,
    - `checkpoint_metric` (or. dti<=X, revol_util<=Y).
- Kod:
  - `src/credit_coach/data/schema.py`
  - `src/credit_coach/storage/models.py`
  - `src/credit_coach/storage/repository.py`

### T2) Weekly optimizer izini kaybetme (trace export)
- Ne eklenecek:
  - `_build_actions_weekly` icindeki her hafta denenen/gereklestirilen guncellemeleri `trajectory_trace` olarak kaydet.
  - Final plan yaninda \"checkpoint timeline\" uret.
- Kod:
  - `src/credit_coach/recourse/generator.py`
  - `src/credit_coach/cli/run_recourse.py`
  - `src/credit_coach/cli/run_batch_recourse_eval.py`

### T3) Musteriye tek liste degil, asamali roadmap ver
- Ne eklenecek:
  - Cikti formati:
    - Ilk 4 hafta: stabilizasyon adimlari
    - 1-3 ay: orta vadeli adimlar
    - 3-6 ay: onay esigi icin son mile adimlari
  - Her asama icin \"beklenen etki\" ve \"yeniden degerlendirme tarihi\".
- Kod:
  - `src/credit_coach/coaching/messaging.py`
  - `src/credit_coach/app/streamlit_app.py`
  - `src/credit_coach/cli/run_recourse.py` (yeni `customer_roadmap.json`)

### T4) Trajectory KPI'lari (yeni)
- Eklenecek KPI'lar:
  - `trajectory_gate_pass_rate_4w`
  - `trajectory_gate_pass_rate_12w`
  - `trajectory_gate_pass_rate_24w`
  - `median_time_to_gate_pass_days`
  - `partial_progress_rate` (approved olmasa da PD dususu hedefi gecenler)
  - `replan_rate` ve `replan_reason_top`
- Kod:
  - `src/credit_coach/cli/run_batch_recourse_eval.py`
  - `src/credit_coach/ops/kpi_contract.py`
  - `configs/kpi_contract.yaml`

### T5) Offline->online baglanti
- Ne eklenecek:
  - Outcome feedback'e \"plan adherence\" ve \"checkpoint completion\" alanlari.
  - Hangi fazda terk oldugu bilgisini logla.
- Kod:
  - `src/credit_coach/cli/run_outcome_feedback.py`
  - `src/credit_coach/data/schema.py`
  - `src/credit_coach/storage/repository.py`

### T6) Gate etkisi (neden metrikleri iyilestirir)
- Beklenen etki:
  - En zor denied vakalarda \"binary approved\" disinda \"ilerleme\" yakalanir.
  - High-risk segmentte tek adim tikanikligi yerine asamali gecis olasiligi artar.
  - Model tarafinda degisim yapmadan dahi uplift izlenebilir hale gelir.

---

## 7) Arastirma Kaynaklari (Secili)

### Recourse ve fairness
- Actionable Recourse in Linear Classification (arXiv): https://arxiv.org/abs/1809.06514
- DiCE paper (arXiv): https://arxiv.org/abs/1905.07697
- DiCE repo: https://github.com/interpretml/DiCE
- FACE (arXiv): https://arxiv.org/abs/1909.09369
- AReS (NeurIPS 2020): https://proceedings.neurips.cc/paper/2020/hash/8ee7730e97c67473a424ccfeff49ab20-Abstract.html
- CARLA benchmark library: https://github.com/carla-recourse/CARLA
- actionable-recourse python package: https://github.com/ustunb/actionable-recourse
- Fairness in Algorithmic Recourse (arXiv 2024): https://arxiv.org/abs/2401.16088
- Longitudinal Counterfactual Explanations (arXiv 2024): https://arxiv.org/pdf/2403.00105

### Fairness postprocessing / metrics
- Equality of Opportunity in Supervised Learning (arXiv): https://arxiv.org/abs/1610.02413
- Fairlearn ThresholdOptimizer docs: https://fairlearn.org/v0.13/user_guide/mitigation/postprocessing.html
- Fairlearn MetricFrame intersecting groups: https://fairlearn.org/main/user_guide/assessment/intersecting_groups.html

### Uncertainty / risk control
- MAPIE repo: https://github.com/scikit-learn-contrib/MAPIE
- MAPIE precision risk control example: https://mapie.readthedocs.io/en/stable/examples_risk_control/1-quickstart/plot_risk_control_binary_classification.html
- MAPIE multi-label risk control example: https://mapie.readthedocs.io/en/latest/examples_risk_control/2-advanced-analysis/plot_risk_control_multi-label_classification.html

### Offline policy evaluation
- Open Bandit Dataset and Pipeline (arXiv): https://arxiv.org/abs/2008.07146
- OBP repo: https://github.com/st-tech/zr-obp

### MLOps / governance / regulation
- SR 11-7 Model Risk Management: https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm
- BCBS 239 Principles: https://www.bis.org/publ/bcbs239.htm
- BCBS 239 progress report (2023): https://www.bis.org/bcbs/publ/d559.htm
- CFPB 2022 black-box adverse action circular/news: https://www.consumerfinance.gov/about-us/newsroom/cfpb-acts-to-protect-the-public-from-black-box-credit-models-using-complex-algorithms/
- CFPB 2023 AI credit denials guidance/news: https://www.consumerfinance.gov/about-us/newsroom/cfpb-issues-guidance-on-credit-denials-by-lenders-using-artificial-intelligence/
- NIST AI RMF 1.0: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10
- Model Cards for Model Reporting: https://arxiv.org/abs/1810.03993

### Telemetry / serving
- OpenTelemetry Python exporters: https://opentelemetry.io/docs/languages/python/exporters/
- OTLP specification: https://opentelemetry.io/docs/specs/otlp/
- OpenTelemetry collector config security best practices: https://opentelemetry.io/es/docs/security/config-best-practices/
- FastAPI server workers: https://fastapi.tiangolo.com/deployment/server-workers/
- Uvicorn deployment docs: https://www.uvicorn.org/
- Prometheus histograms and summaries: https://prometheus.io/docs/practices/histograms/
- Prometheus instrumentation best practices: https://prometheus.io/docs/practices/instrumentation/

### Model constraints
- XGBoost monotonic constraints: https://xgboost.readthedocs.io/en/stable/tutorials/monotonic.html
- XGBoost parameters (`monotone_constraints`): https://xgboost.readthedocs.io/en/latest/parameter.html

---

## 8) Kodlamaya Gecis Oncesi Karar Notu
Bu plan dogrudan kodlanabilir.
Kodlamaya gecis sirasinda once P0 altindaki Faz-1 uygulanacak:
1. A1 + A2 + A3
2. B1
3. C1

Her alt-adimdan sonra zorunlu test:
- Unit + integration + `run_phase_experiment_suite --execute` (200 ve 1000x5)
- Sonuc raporu `docs/` altina faz bazli yazilacak.
