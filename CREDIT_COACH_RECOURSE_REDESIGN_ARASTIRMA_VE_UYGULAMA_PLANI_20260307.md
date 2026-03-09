# CREDIT COACH RECOURSE REDESIGN - ARASTIRMA VE UYGULAMA PLANI

## Surum
- Dokuman tarihi: `2026-03-07`
- Kapsam: `Recourse motorunun gate-pass odakli yeniden tasarimi`
- Durum: `Arastirma + plan (kod degisikligi yapilmadi)`

---

## 1) Problem Tanimi (Mevcut Durum)
1000 musteri batch testinde su tablo goruldu:
1. `DiCE technical success = 100%` (fallback yok)
2. `Denied -> Approved lift = 0`
3. `before_approval_rate == after_approval_rate`

Cikarim:
1. Sorun entegrasyon degil, optimizasyon hedefinin is karar gate'leriyle hizalanmamasi.
2. Sistem plan uretiyor ama gate'i gecen plan uretiminde (ozellikle base PD > tau segmentinde) yetersiz.

Ilgili mevcut kod:
1. [generator.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/recourse/generator.py)
2. [validator.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/safety/validator.py)
3. [run_batch_recourse_eval.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py)

---

## 2) Arastirma Ozetleri (Makale + Repo + Official Docs)

### 2.1 Recourse temel literaturu
1. Ustun et al. (FAccT 2019) - actionable recourse ve feasibility audit
2. Karimi et al. (NeurIPS 2020) - imperfect causal knowledge altinda probabilistic recourse
3. Karimi et al. (FAccT 2021) - recourse'u counterfactualdan intervention seviyesine tasima
4. Karimi et al. (ACM CSUR 2022) - algorithmic recourse survey
5. Upadhyay et al. (NeurIPS 2021) - model shift altinda robust recourse (ROAR)
6. Dominguez-Olmedo et al. (ICML 2022) - adversarially robust causal recourse
7. Pawelczyk et al. (UAI 2020) - predictive multiplicity altinda recourse kirilganligi
8. von Kugelgen et al. (AAAI 2022) - causal recourse fairness boyutu

### 2.2 Recoourse tooling / benchmark ekosistemi
1. DiCE (repo + docs): `random/genetic/kdtree`, `features_to_vary`, `permitted_range`, `feature_weights`
2. CARLA: recourse/counterfactual benchmark kutuphanesi
3. actionable-recourse (ustunb): linear model feasibility + cost audit
4. Alibi Explain: CFI/CFProto/CFRL counterfactual yaklasimlari
5. Fairlearn: group fairness metrikleri ve trade-off dokumantasyonu

### 2.3 Model ve belirsizlik
1. XGBoost monotonic constraints + interaction constraints
2. SHAP TreeExplainer (`interventional/tree_path_dependent`, additivity checks)
3. CalibratedClassifierCV (isotonic/sigmoid)
4. MAPIE (2026 itibariyla aktif): conformal prediction intervals/sets + risk control

### 2.4 Sektorel yonetisim
1. Fed SR 11-7 / OCC 2011-12 model risk guidance
2. BCBS 239 risk data aggregation/reporting
3. NIST AI RMF 1.0 + Playbook
4. OWASP API Security Top 10 (2023)

---

## 3) Teknik Tasarim (8 Madde Icin Arastirma-Temelli Plan)

## 3.1 P0 - Objective'i gate ile hizalama
Arastirma dayanaklari:
1. Ustun 2019: feasibility ve cost audit'in recourse kalitesinde merkezi rolu
2. Karimi 2020/2021: causal/probabilistic reliability
3. ROAR/PROBE cizgisi: robustluk maliyeti explicit objective olmali

Yeni objective (onerilen):
\[
J(x') =
 w_{ci} \max(0, CI_{high}(x')-\tau)
+ w_{rel} \max(0, r_{min}-R(x'))
+ w_{worst} \max(0, m_{min}-M_{worst}(x'))
+ w_{cost} C(x,x')
+ w_{sparse} S(x,x')
+ w_{fair} \Delta_{fair}(x')
\]

Burada:
1. `CI_high <= tau` ve robust gate terimleri objective'in birinci sinif vatandasi olur.
2. Mevcut skor (`tau - pred_pd`) tek basina degil, gate ihlal cezasi ile optimize edilir.

Kod etki alani:
1. [generator.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/recourse/generator.py)
2. [validator.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/safety/validator.py)
3. [coaching/planner.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/coaching/planner.py)

Test/acceptance:
1. `base_pd > tau` segmentinde `denied_with_gate_pass_plan` artmali.
2. `approval_gap_delta <= +0.01` korunmali.

---

## 3.2 P0 - Adaptive step optimizer
Arastirma dayanaklari:
1. DiCE docs: proximity/diversity/sparsity agirliklarinin etkisi
2. Ustun recourse: action set + direction + bounds
3. XGBoost monotonic constraints: feature direction bilgisi ile tutarli arama

Plan:
1. Sabit `spec.step` yerine kisiye ve hedefe duyarli step schedule:
   - `step_0 = spec.step`
   - gate gecmiyorsa geometrik artirim (`x1.5`, `x2`) + max bound
2. Feature bazli risk-duyarli step:
   - PD gradyani yuksek feature'larda daha buyuk ilk deneme
3. Feasibility-first clipping:
   - immutable, direction, bounds en basta uygulanir

Kod etki alani:
1. [generator.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/recourse/generator.py)
2. [action_space.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/recourse/action_space.py)
3. [configs/recourse.yaml](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/configs/recourse.yaml)

Yapilandirma (yeni):
1. `adaptive_steps.enabled`
2. `adaptive_steps.max_multiplier`
3. `adaptive_steps.growth_factor`
4. `adaptive_steps.max_attempts_per_feature`

---

## 3.3 P0 - Denied-target mode
Arastirma dayanaklari:
1. Strategic behavior literaturu (NeurIPS 2020) ve recourse reliability calismalari: tek policy herkese uygun degil
2. Batch bulgusu: denied segmentte `approved_plan_count = 0`

Plan:
1. `if base_pd > tau + delta`: denied-target mode aktif
2. Bu modda:
   - daha fazla candidate (`beam_width`, `max_actions`, `total_cfs`)
   - daha uzun horizon agirligi
   - daha genis `features_to_vary`
3. Search budget zaman limiti ile sinirlanir (latency patlamasi kontrolu)

Kod etki alani:
1. [run_batch_recourse_eval.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py)
2. [run_recourse.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/cli/run_recourse.py)
3. [configs/recourse.yaml](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/configs/recourse.yaml)

Yeni funnel metrikleri zorunlu:
1. `denied_count`
2. `denied_with_any_candidate`
3. `denied_with_gate_pass_plan`
4. `denied_to_approved_lift`

---

## 3.4 P1 - Belirsizlik modelini guclendirme
Arastirma dayanaklari:
1. Conformal prediction (Shafer/Vovk, CQR)
2. MAPIE (2026 guncel): model-agnostic uncertainty + risk control

Plan:
1. Simdiki normal bootstrap CI'ya ek olarak conformal CI/sets modulu
2. Opsiyonlar:
   - split conformal
   - jackknife+
   - mondrian conformal (grup-bazli coverage icin)
3. Validator gate'i:
   - `CI_high_conformal <= tau` birincil, bootstrap ikincil check

Kod etki alani:
1. [statistical.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/safety/statistical.py)
2. [validator.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/safety/validator.py)
3. [requirements.txt](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/requirements.txt)

---

## 3.5 P1 - DiCE + internal planner birlesik havuz
Arastirma dayanaklari:
1. DiCE method farkliliklari (random/genetic/kdtree) trade-off
2. Predictive multiplicity calismalari: tek model/tek yontem recourse kirilgan olabilir
3. CARLA: coklu recourse yontemi benchmark gerekliligi

Plan:
1. Candidate pool = `internal + dice_random + dice_genetic + dice_kdtree`
2. Rerank kriteri:
   - gate-pass olasiligi
   - robust margin
   - cost/sparsity
3. Dominance pruning:
   - daha pahali ve daha riskli planlar elenir

Kod etki alani:
1. [dice_baseline.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/recourse/dice_baseline.py)
2. [planner.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/coaching/planner.py)
3. [run_recourse.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/cli/run_recourse.py)

---

## 3.6 P0 - Funnel metrikleri ve operasyonel telemetry
Arastirma dayanaklari:
1. SR11-7: outcome analysis + ongoing monitoring
2. BCBS239: risk data aggregation dogrulugu/izlenebilirligi
3. OpenTelemetry/Prometheus best-practice: stable metric schema

Plan:
1. Batch ve online recourse akisi icin standard metric set
2. Her adimda counters:
   - `candidate_generated`
   - `candidate_feasible`
   - `candidate_gate_pass`
   - `served_recommendation`
3. Latency dagilimi:
   - p50/p95/p99 + outlier (>1s, >5s)

Kod etki alani:
1. [run_batch_recourse_eval.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py)
2. [ops/telemetry.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/ops/telemetry.py)
3. [run_monitoring.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/cli/run_monitoring.py)

---

## 3.7 P1 - Fairness-regulated recourse
Arastirma dayanaklari:
1. Hardt et al. EO (NeurIPS 2016)
2. Fairlearn metrics and trade-off caveats
3. On the Fairness of Causal Algorithmic Recourse (AAAI 2022)

Plan:
1. Recourse objective icine fairness penalty ekle:
   - grup bazli local uplift dengesizligi cezasi
2. Post-selection fairness filter:
   - teklif edilen plan setinin `approval_gap_delta` etkisi hesaplanir
3. Stress senaryolarinda fairness robustlugu zorunlu metric olur

Kod etki alani:
1. [evaluation/fairness.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/evaluation/fairness.py)
2. [run_fairness.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/cli/run_fairness.py)
3. [generator.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/recourse/generator.py)

---

## 3.8 P0 - KPI contract ve release gate
Hedef KPI (pilot):
1. `denied_to_approved_lift >= 0.05`
2. `approval_gap_delta <= +0.01`
3. `equalized_odds_gap_delta <= +0.01`
4. `p95 <= 500ms`, `p99 <= 2000ms`
5. `error_rate <= 0.005`

Release gate'e eklenecek kararlar:
1. Lift KPI tutmazsa release `NO-GO`
2. Fairness KPI bozulursa release `NO-GO`
3. SLO ihlali varsa release `CONDITIONAL` veya `NO-GO`

Kod etki alani:
1. [run_production_smoke.py](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/src/credit_coach/cli/run_production_smoke.py)
2. [docs/RELEASE_GATES.md](/Users/bkoseoglu/Desktop/Bitirme/05032026/credit-coach/docs/RELEASE_GATES.md)

---

## 4) Fazli Uygulama Yol Haritasi (Sonraki Asama Uygulamasi Icin)

## Faz-1 (P0, 1-2 hafta)
1. Gate-aligned objective
2. Denied-target mode
3. Funnel metrics (batch + online)

Cikis kriteri:
1. 1000 batch testte `denied_with_gate_pass_plan > 0`
2. `error_rate <= 0.5%`

## Faz-2 (P0/P1, 2 hafta)
1. Adaptive step optimizer
2. Hybrid candidate pool (internal + DiCE)

Cikis kriteri:
1. `denied_to_approved_lift >= 2%` (ara hedef)
2. p95 latency <= 700ms

## Faz-3 (P1, 2 hafta)
1. Conformal uncertainty (MAPIE)
2. Fairness-regulated reranking

Cikis kriteri:
1. `denied_to_approved_lift >= 5%`
2. `approval_gap_delta <= +0.01`

## Faz-4 (P0, 1 hafta)
1. Release gate entegrasyonu
2. Dokumantasyon + runbook + backtesting refresh

Cikis kriteri:
1. Smoke gate `GO`
2. KPI contract tumu PASS

---

## 5) Deney Tasarimi (Uygulamadan Sonra Calisacak)
1. A/B setup:
   - A: mevcut recourse
   - B: redesign
2. Segment bazli olcum:
   - `base_pd <= tau`
   - `tau < base_pd <= tau+0.05`
   - `base_pd > tau+0.05`
3. Zorunlu cikti dosyalari:
   - `batch_recourse_results.csv`
   - `recourse_funnel_summary.csv`
   - `fairness_stress_compare.csv`
   - `latency_outliers.csv`
4. Statistical test:
   - lift icin bootstrap CI
   - fairness delta icin paired test

---

## 6) Riskler ve Teknik Borc Notlari
1. Trade-off riski: lift artisi fairness'i bozabilir (Pareto yonetimi gerekli)
2. Conformal entegrasyonda performans maliyeti olabilir
3. DiCE multi-method pool latency kuyruklarini uzatabilir (budget + timeout zorunlu)
4. SR11-7 baglaminda model inventory + validation raporlari release'e baglanmali

---

## 7) Uygulama Oncesi Karar Listesi
Kodlamaya gecmeden once netlestirilecekler:
1. Pilot KPI'nin resmi hedefleri (`lift`, fairness delta, latency SLO)
2. Denied-target mode icin max operasyonel butce (satir basi ms limiti)
3. Fairness metric onceligi (`approval_gap` vs `equalized_odds` agirliklari)
4. Conformal yontem tercihi (`split`, `jackknife+`, `mondrian`)

---

## 8) Kaynaklar
1. Actionable Recourse (FAccT 2019): https://doi.org/10.1145/3287560.3287566
2. Algorithmic Recourse under Imperfect Causal Knowledge (NeurIPS 2020): https://proceedings.neurips.cc/paper/2020/hash/02a3c7fb3f489288ae6942498498db20-Abstract.html
3. Algorithmic Recourse: from Counterfactual Explanations to Interventions (FAccT 2021): https://doi.org/10.1145/3442188.3445899
4. A Survey of Algorithmic Recourse (ACM CSUR 2022): https://dl.acm.org/doi/10.1145/3527848
5. Towards Robust and Reliable Algorithmic Recourse (NeurIPS 2021): https://proceedings.neurips.cc/paper/2021/hash/8ccfb1140664a5fa63177fb6e07352f0-Abstract.html
6. On the Adversarial Robustness of Causal Algorithmic Recourse (ICML 2022): https://proceedings.mlr.press/v162/dominguez-olmedo22a.html
7. On Counterfactual Explanations under Predictive Multiplicity (UAI 2020): https://proceedings.mlr.press/v124/pawelczyk20a.html
8. On the Fairness of Causal Algorithmic Recourse (AAAI 2022): https://doi.org/10.1609/aaai.v36i9.21192
9. Decisions, Counterfactual Explanations and Strategic Behavior (NeurIPS 2020): https://proceedings.neurips.cc/paper/2020/hash/c2ba1bc54b239208cb37b901c0d3b363-Abstract.html
10. DiCE repo/docs: https://github.com/interpretml/DiCE
11. DiCE method docs (random/genetic/kdtree): https://interpret.ml/DiCE/notebooks/DiCE_model_agnostic_CFs.html
12. CARLA recourse benchmark: https://github.com/carla-recourse/CARLA
13. actionable-recourse repo: https://github.com/ustunb/actionable-recourse
14. Alibi Explain docs: https://docs.seldon.ai/alibi-explain
15. XGBoost monotonic constraints tutorial: https://xgboost.readthedocs.io/en/stable/tutorials/monotonic.html
16. SHAP TreeExplainer docs: https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html
17. scikit-learn calibration docs: https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV
18. MAPIE repo/docs: https://github.com/scikit-learn-contrib/MAPIE
19. MAPIE risk control examples: https://mapie.readthedocs.io/en/stable/examples_risk_control/index.html
20. Fairlearn common fairness metrics: https://fairlearn.org/v0.12/user_guide/assessment/common_fairness_metrics.html
21. Equality of Opportunity (NeurIPS 2016): https://proceedings.neurips.cc/paper/2016/hash/9d2682367c3935defcb1f9e247a97c0d-Abstract.html
22. SR 11-7 (Fed): https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm
23. OCC 2011-12: https://www.occ.treas.gov/news-issuances/bulletins/2011/bulletin-2011-12.html
24. BCBS 239: https://www.bis.org/publ/bcbs239.htm
25. NIST AI RMF 1.0: https://doi.org/10.6028/NIST.AI.100-1
26. NIST SP 1270 (bias): https://doi.org/10.6028/NIST.SP.1270
27. OWASP API Security Top 10 (2023): https://owasp.org/API-Security/editions/2023/en/0x11-t10/

