# CREDIT COACH FINTECH URETIM GELISTIRME: ARASTIRMA + DETAYLI TEKNIK PLAN

## Surum
- Dokuman surumu: `v1.0`
- Tarih: `2026-03-07`
- Kapsam: `Recourse kalitesi + XAI derinligi + stress/fairness/backtesting + guvenlik + operasyonel izleme`
- Hedef: `Sistemi demo/prototype seviyesinden fintech urun seviyesine cikarmak`

---

## 1) Mevcut Durum Ozeti (Kod + Son Calismalar)

### 1.1 Guclu taraflar
1. Gate-pass odakli recourse tasarimi uygulanmis:
   - `denied_target`, `adaptive_steps`, `hybrid pool (internal + DiCE)`
   - Dosyalar: `src/credit_coach/recourse/generator.py`, `src/credit_coach/cli/run_batch_recourse_eval.py`, `src/credit_coach/coaching/planner.py`
2. Funnel metrikleri var:
   - `denied_count`, `denied_with_any_candidate`, `denied_with_gate_pass_plan`, `denied_to_approved_lift`
3. Fairness ve stress raporlama var:
   - `batch_fairness_change.csv`, `batch_fairness_stress_compare.csv`
4. Release gate iskeleti var:
   - `run_production_smoke.py`, `docs/RELEASE_GATES.md`

### 1.2 Kritik darbogazlar
1. **Latency (P0):**
   - 500 batch, 5 worker kosusunda: `p95 ~ 5909 ms`, `p99 ~ 28193 ms` (hedefin cok uzerinde).
2. **Recourse uygulanabilirligi (P0/P1):**
   - Internal planlarin buyuk bolumu `10 aksiyon` seviyesinde; pratik uygulanabilirlik riski.
3. **Belirsizlik modeli (P0):**
   - `safety/statistical.py` icindeki conformal CI su an residual kalibrasyon datasina dayanmayan basit proxy.
4. **Causal katman (P1):**
   - `rex_runner.py` korelasyon tabanli kenar uretimi yapiyor; nedensellik kaniti zayif.
5. **Guvenlik/uyum (P0):**
   - API guvenlik temel seviyede; fintech-grade secrets, IAM, immutable logging, model governance genisletilmeli.

---

## 2) Arastirma Bulgulari: Akademik ve Sektorel Karsilik

## 2.1 Recourse literaturu ve bu projeye etkisi
1. **Actionable Recourse in Linear Classification (Ustun et al., FAccT 2019):**
   - Recourse'un eylem maliyeti ve uygulanabilir kisitlarla optimize edilmesi gerektigini vurgular.
   - Etki: Plan seciminde sadece PD degisimi degil, aksiyon maliyeti + kisitlar + bireysel feasibility zorunlu.
2. **DiCE (Mothilal et al., FAT* 2020 / arXiv 1905.07697):**
   - Diverse counterfactual ureterek aday havuzu genisletir.
   - Etki: Tek method yerine `random + genetic + kdtree` kombinasyonu ile kapsama artar.
3. **FACE (Poyiadzi et al., AIES 2020 / arXiv 1909.09369):**
   - Data manifold uzerinden feasible/actionable counterfactual onerir.
   - Etki: Synthetic ama gercek-disi hareketleri azaltmak icin manifold yaklasimi eklenmeli.
4. **CARLA benchmark (Pawelczyk et al., NeurIPS Datasets & Benchmarks 2021):**
   - Recourse yontemlerini standard metriclerle karsilastirma altyapisi saglar.
   - Etki: Validity/proximity/sparsity/diversity/feasibility metrikleri standart hale getirilmeli.
5. **Recourse Verification (arXiv 2308.12820):**
   - Recourse'un formal olarak dogrulanmasi gerektigini gosterir.
   - Etki: "buldu" yerine "garanti etti" seviyesine gecis icin dogrulama testi gerekir.
6. **Longitudinal counterfactuals (arXiv 2403.00105):**
   - Tek adimli onerilerin zamanla bozulabilecegini, cok-adimli/sekansiyel tasarimin onemini vurgular.
   - Etki: Haftalik coaching loop ile sekansiyel recourse birlestirilmeli.

## 2.2 Belirsizlik, risk kontrolu, model kalibrasyon
1. **MAPIE (official docs + repo):**
   - Conformal prediction ile coverage odakli belirsizlik kontrolu saglar.
   - Etki: Su anki proxy CI yerine holdout residual tabanli gercek conformal pipeline kurulmali.
2. **XGBoost monotonic constraints (official docs):**
   - Domain bilgisine uygun monotonicity ile model davranisi daha stabil yapilabilir.
   - Etki: Kredi riskinde beklenen yon etkileri (orn. gelir artisi PD'yi artirmamali) kodlanmali.
3. **SHAP TreeExplainer docs:**
   - Model output ve background secimi dogru yapilmadiginda aciklanabilirlik sapabilir.
   - Etki: SHAP reliability pack (stability, background governance) zorunlu olmali.

## 2.3 Fairness/Regulasyon/Model Risk
1. **Fairlearn docs:**
   - Grup bazli fairness metriklerinin dogru okunmasi ve trade-off yonetimi.
2. **Federal Reserve SR 11-7:**
   - Model risk management: inventory, validation, outcomes analysis, ongoing monitoring.
3. **BCBS 239 (BIS):**
   - Risk data aggregation ve reporting prensipleri.
4. **EU AI Act (Regulation (EU) 2024/1689):**
   - Kredi skorlama yuksek risk kapsaminda; ana uygulama tarihi: `2 Agustos 2026`.
5. **CFPB adverse action guidance (Circular 2022-03 + 2023 statement):**
   - "Karmasik algoritma" gerekcesiyle aciklama yukumlulugu kalkmaz.

Sonuc: Projenin cekirdegi akademik olarak dogru yonde; ancak fintech urun seviyesinde **belirsizlik kalibrasyonu, recourse feasibility, latency, governance/compliance** taraflari daha derinlesmeli.

---

## 3) Adim Adim Gap Analizi (Mevcut -> Gerekli)

| Alan | Mevcut | Gap | Oncelik |
|---|---|---|---|
| Recourse objective | Gate odakli skor var | Plan gercekciligi ve action budget sert degil | P0 |
| Aday uretimi | Internal + DiCE var | Manifold/causal feasibility zayif | P0 |
| Uncertainty | Bootstrap + proxy conformal | True conformal calibration yok | P0 |
| Fairness | Approval/eo gap var | Recourse-specific fairness metrikleri eksik | P1 |
| Stress/backtest | Temel matrix + benchmark var | Rolling/temporal robustness derinligi eksik | P0 |
| Latency/SRE | Basic telemetry var | p95/p99 hedef disi, queue/backpressure yok | P0 |
| Security | Token + rate-limit var | Secrets, IAM, audit immutability, data protection yetersiz | P0 |
| Compliance | Gate/report var | Adverse-action reasoning ve model governance pack eksik | P0 |

---

## 4) Detayli Uygulama Plani (Kodlama Oncesi Nihai Taslak)

## Faz-0 (P0) Baseline ve Olcum Kontrati (3-4 gun)
1. KPI contract sabitle:
   - `denied_to_approved_lift >= 0.05`
   - `approval_gap_delta <= +0.01`
   - `latency_p95 <= 500ms`, `p99 <= 2000ms`
   - `error_rate <= 0.5%`
2. Batch raporlarina zorunlu ekler:
   - recourse cost percentiles
   - action count distribution
   - not-approved denied root-cause taxonomy
3. Reproducibility:
   - run manifest + config hash + dataset hash zorunlu.

Cikis kriteri:
- KPI contract ve metric dictionary freeze edilmis olacak.

## Faz-1 (P0) Recourse Motoru: Gate-pass + Feasibility Sertlestirme (1-1.5 hafta)
1. Objective revizyonu:
   \[
   \max_x\; S(x')=w_1(\tau-CI_{high}) + w_2\,Rel(x') + w_3\,WorstMargin(x') - w_4\,Cost(x,x') - w_5\,FairPenalty
   \]
   Kosullar:
   - `CI_high <= tau`
   - `Rel >= min_rel`
   - `WorstMargin >= min_margin`
2. Action budget kurali:
   - soft penalty yerine hard cap (`max_actions_denied`, `max_actions_regular`).
   - action_count > cap ise plan otomatik elensin.
3. Denied-target mode v2:
   - daha genis search ama strict feasibility.
   - time budget + early-stop + candidate pruning.
4. Planner tie-break:
   - `APPROVED` > `gate margin` > `fewer actions` > `lower cost` > `lower PD`.

Kod dokunuslari:
- `src/credit_coach/recourse/generator.py`
- `src/credit_coach/coaching/planner.py`
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `configs/recourse.yaml`

Testler:
- yeni unit: action budget, tie-break, denied-mode edge cases.
- batch smoke: 200/500 cohort.

Cikis kriteri:
- Denied segmentte gate-pass oraninda dusus olmadan action_count medyaninin azalmasi.

## Faz-2 (P0) True Conformal + Uncertainty Calibration (1 hafta)
1. Holdout residual pipeline:
   - calibration split uzerinden nonconformity score hesapla.
   - quantile ile sample-aware interval kur.
2. MAPIE entegrasyonu (opsiyonel ilk adim):
   - classifier set prediction ve risk-coverage monitoring.
3. Hybrid policy:
   - high stress: daha konservatif alpha + interval.

Kod dokunuslari:
- `src/credit_coach/safety/statistical.py`
- `src/credit_coach/safety/validator.py`
- `src/credit_coach/cli/run_train.py` (calibration artifact yazimi)
- `configs/safety.yaml`

Testler:
- calibration coverage test (`target_coverage +/- tolerance`).
- scenario bazli CI stability test.

Cikis kriteri:
- CI coverage raporu release artefakti olacak.

## Faz-3 (P0/P1) Model + XAI Derinlestirme (1 hafta)
1. XGBoost production profile:
   - monotonic constraints domain kurallariyla eslestir.
   - deterministic seeds + version pin.
2. SHAP reliability pack:
   - background governance
   - local explanation stability score
   - SHAP drift takibi.
3. Adverse action reason engine:
   - top reason mapping + regu riskli ifadeleri filtreleme.

Kod dokunuslari:
- `src/credit_coach/model/train.py`
- `src/credit_coach/xai/shap_local.py`
- `src/credit_coach/coaching/messaging.py`
- `configs/model.yaml`

Testler:
- monotonicity regression tests.
- explanation consistency tests.

Cikis kriteri:
- Adverse-action nedeni deterministic ve audit edilebilir.

## Faz-4 (P0) Stress/Fairness/Backtesting Lab (1-1.5 hafta)
1. Rolling window backtest genislet:
   - multi-window + OOT slices + macro regime tagging.
2. Recourse-specific fairness metricleri:
   - `recourse_success_gap`
   - `avg_recourse_cost_gap`
   - `time_to_approval_gap`
3. Stress x fairness matrix:
   - high stress altinda recourse success parity kontrolu.

Kod dokunuslari:
- `src/credit_coach/evaluation/fairness.py`
- `src/credit_coach/cli/run_fairness.py`
- `src/credit_coach/cli/run_benchmark.py`

Testler:
- fairness stress matrix regression test.
- rolling window gate test.

Cikis kriteri:
- fairness bozulmadan lift korunmali (Pareto raporu zorunlu).

## Faz-5 (P0) Latency ve Operasyonel Sertlestirme (1 hafta)
1. Profiling:
   - row-level timer breakdown: internal generation, validation, DiCE, I/O.
2. Pipeline optimizasyonu:
   - process-based parallelization secenegi (`ProcessPool`) ve worker warm-up.
   - DiCE budget/timeouts.
   - internal plan batch scoring vectorization.
3. SLO odakli izleme:
   - Prometheus histogram bucketlar (`latency_ms_bucket`).
   - error taxonomy + retry policy.

Kod dokunuslari:
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `src/credit_coach/ops/telemetry.py`
- `configs/monitoring.yaml`

Testler:
- load test: 1000 customer @1, @5 workers.

Cikis kriteri:
- `p95 <= 500ms`, `p99 <= 2000ms` (hedef).

## Faz-6 (P0) Guvenlik, Uyum ve Release Governance (1 hafta)
1. API security hardening:
   - key rotation automation
   - secret source = env/secret manager, dosyada plain key yok
   - endpoint RBAC ayrimi.
2. Audit hardening:
   - hash chain + signed release manifest.
3. Compliance pack:
   - model card
   - adverse action template
   - monitoring + governance report bundle.
4. Go/No-Go komitesi:
   - SR11-7 mantigina uygun challenger/champion + override log.

Kod dokunuslari:
- `src/credit_coach/api/auth.py`
- `src/credit_coach/storage/repository.py`
- `src/credit_coach/cli/run_production_smoke.py`
- `docs/PROD_RUNBOOK.md`, `docs/RELEASE_GATES.md`

Testler:
- security tests + audit verify + smoke gates.

Cikis kriteri:
- Tum gate PASS -> GO.

---

## 5) Sektorel ve Akademik Karsilik Degerlendirmesi

1. **Model + recourse cekirdegi:** Akademik olarak guclu tabana sahip (DiCE/FACE/Actionable Recourse ile uyumlu).
2. **Uretim guvenilirligi:** Sektorel beklentinin altinda (SLO, governance, compliance dokumani derinligi artmali).
3. **Regulasyon hazirligi:** Iskelet var ama fintech-grade degil; CFPB adverse action ve AI Act high-risk gereklilikleri icin dokumante aciklama/izlenebilirlik sertlestirilmeli.
4. **Sonuc:** Metodoloji degismeli degil, **derinlestirilmeli ve sertlestirilmeli**.

---

## 6) Kodlama Fazina Gecis Icin Net Uygulama Sirasi

1. Faz-1 (Recourse feasibility + planner tie-break + action budget)
2. Faz-2 (True conformal calibration)
3. Faz-5 (Latency optimizasyonu)
4. Faz-4 (Fairness/backtesting derinligi)
5. Faz-3 (XGBoost/SHAP reliability)
6. Faz-6 (Security/compliance/release governance)

Not: Oncelik sirasi, mevcut en kritik release blocker olan `latency + recourse realism + uncertainty credibility` uzerinden belirlenmistir.

---

## 7) Kaynaklar (Birincil)

1. Actionable Recourse in Linear Classification (FAccT 2019): https://dl.acm.org/doi/10.1145/3287560.3287566
2. DiCE paper (arXiv 1905.07697): https://arxiv.org/abs/1905.07697
3. DiCE official docs (model-agnostic CF): https://interpret.ml/DiCE/notebooks/DiCE_model_agnostic_CFs.html
4. DiCE GitHub repo: https://github.com/interpretml/DiCE
5. FACE paper (arXiv 1909.09369): https://arxiv.org/abs/1909.09369
6. CARLA benchmark repo: https://github.com/carla-recourse/CARLA
7. Recourse verification (arXiv 2308.12820): https://arxiv.org/abs/2308.12820
8. Longitudinal counterfactuals (arXiv 2403.00105): https://arxiv.org/abs/2403.00105
9. MAPIE repo: https://github.com/scikit-learn-contrib/MAPIE
10. MAPIE docs: https://mapie.readthedocs.io/en/latest/
11. XGBoost monotonic constraints docs: https://xgboost.readthedocs.io/en/stable/tutorials/monotonic.html
12. SHAP TreeExplainer docs: https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html
13. Fairlearn fairness metrics docs: https://fairlearn.org/v0.12/user_guide/assessment/common_fairness_metrics.html
14. OpenTelemetry Python exporters docs: https://opentelemetry.io/docs/languages/python/exporters/
15. Prometheus histogram best practices: https://prometheus.io/docs/practices/histograms/
16. FastAPI workers deployment docs: https://fastapi.tiangolo.com/deployment/server-workers/
17. Federal Reserve SR 11-7: https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm
18. BIS BCBS 239 principles: https://www.bis.org/publ/bcbs239.htm
19. EU AI Act official text (Regulation (EU) 2024/1689): https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng
20. CFPB Circular 2022-03: https://www.consumerfinance.gov/compliance/circulars/consumer-financial-protection-circular-2022-03-adverse-action-notification-requirements-in-connection-with-credit-decisions-based-on-complex-algorithms/
21. CFPB statement (2023-03) on automated credit denials: https://files.consumerfinance.gov/f/documents/cfpb_statement_credit-denials-automated-algorithms_2023-03.pdf
