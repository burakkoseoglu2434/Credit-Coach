# CREDIT COACH 12 HAFTA UYGULAMA RAPORU

## 0) Referans ve amac
Bu uygulama raporu su referans dokuman baz alinarak hazirlandi:
- `CREDIT_COACH_12_HAFTA_AGENT_MASTER_PLAN.md`

Amac:
1. 12 haftalik sureci kod tarafinda adim adim ilerletmek.
2. Her adimda test/komut calistirip sonucu kaydetmek.
3. Uretilen artifact ve metrikleri hafta bazli belgelemek.

Not:
- Calisma ortami sinirlari nedeniyle model backend otomatik olarak `logistic_regression` fallback ile calistirildi.
- Pipeline sozlesmesi mevcut kod tabanina uyumlu olacak sekilde `47 feature + 1 target` olarak korundu.

---

## 1) Baslangic durumu (oncesi)
Baslangicta calisan kisimlar:
- Hafta 1 iskeleti: dry-run, feature lock, action space, DB katmani
- Mevcut testler: `test_feature_lock.py`, `test_action_space.py`

Ilk baseline test:
- Komut: `cd credit-coach && pytest -q`
- Sonuc: `29 passed`

---

## 2) Hafta hafta gelistirme, test ve ciktilar

## Hafta 1 - Iskelet dogrulama
Gelisitirilen/korunan moduller:
- `src/credit_coach/cli/run_train.py` (dry-run + gercek train akisi)
- `src/credit_coach/storage/*`, `src/credit_coach/data/schema.py`

Calistirilan komut:
- `python -m credit_coach.cli.run_train --dry_run`

Sonuc:
- Run ID: `20260306_231646_0e8e25`
- Dry run basarili
- DB, import ve feature lock kontrolleri gecti

Test:
- Hafta 1 testleri (feature lock + action space) genel pytest icinde gecti.

---

## Hafta 2 - Ingest, preprocess, split
Eklenen dosyalar:
- `src/credit_coach/data/ingest.py`
- `src/credit_coach/data/preprocess.py`
- `src/credit_coach/data/features.py`
- `src/credit_coach/data/split.py`
- `src/credit_coach/cli/run_prepare_data.py`
- `configs/default.yaml` (prepare_data + raw_csv parametreleri)

Calistirilan komut:
- `python -m credit_coach.cli.run_prepare_data --config configs/default.yaml --sample_rows 20000`

Ciktilar:
- Run ID: `20260306_231645_005e7d`
- `data/processed/train.parquet`
- `data/processed/test.parquet`
- `data/splits/split_summary.json`

Metrikler (`artifacts/runs/20260306_231645_005e7d/metrics.json`):
- rows_total: 20000
- rows_train: 16000
- rows_test: 4000
- feature_count: 47
- categorical_encoded: 16

Test:
- `tests/test_data_pipeline.py` eklendi ve gecti.

---

## Hafta 3 - Model train, calibration, registry
Eklenen dosyalar:
- `src/credit_coach/model/train.py`
- `src/credit_coach/model/calibrate.py`
- `src/credit_coach/model/evaluate.py`
- `src/credit_coach/model/predict.py`
- `src/credit_coach/model/registry.py`
- `src/credit_coach/model/__init__.py`
- `configs/model.yaml` guncellendi (`n_jobs: 1`)

Calistirilan komut:
- `python -m credit_coach.cli.run_train --config configs/model.yaml`

Ciktilar:
- Run ID: `20260306_231650_0e8e25`
- Model bundle:
  - `artifacts/models/20260306_231650_0e8e25/model.joblib`
  - `artifacts/models/20260306_231650_0e8e25/calibrator.joblib`
  - `artifacts/models/20260306_231650_0e8e25/metrics.json`
  - `artifacts/models/latest.json`

Metrikler:
- auc: 0.9571
- pr_auc: 0.8314
- f1: 0.7927
- brier: 0.0614
- ece: ~0
- ks: 0.8109
- backend: logistic_regression

Test:
- `tests/test_model_pipeline.py` eklendi ve gecti.

---

## Hafta 4 - Local explanation (explain only)
Eklenen dosyalar:
- `src/credit_coach/xai/shap_global.py`
- `src/credit_coach/xai/shap_local.py`
- `src/credit_coach/xai/__init__.py`

Calistirilan komut:
- `python -m credit_coach.cli.run_recourse --customer_id demo --row_index 5 --explain_only`

Cikti:
- Run ID: `20260306_231713_b9ad0c`
- `artifacts/runs/20260306_231713_b9ad0c/tables/local_reasons.json`

Test:
- XAI akisi recourse CLI icinde smoke olarak calisti.

---

## Hafta 5 - Causal graph ve constraint
Eklenen dosyalar:
- `src/credit_coach/causality/rex_runner.py`
- `src/credit_coach/causality/graph_utils.py`
- `src/credit_coach/causality/action_constraints.py`
- `src/credit_coach/causality/__init__.py`

Uretilen DAG:
- `artifacts/models/causal_graph.json`
- node sayisi: 47
- edge sayisi: 267
- algorithm: pc

Test:
- `tests/test_rex_constraints.py` eklendi ve gecti.

---

## Hafta 6 - Recourse generator (9 plan)
Eklenen dosyalar:
- `src/credit_coach/recourse/generator.py`
- `src/credit_coach/recourse/region_targets.py`
- `src/credit_coach/recourse/dice_baseline.py`
- `src/credit_coach/coaching/planner.py`
- `src/credit_coach/cli/run_recourse.py`

Calistirilan komut:
- `python -m credit_coach.cli.run_recourse --customer_id demo --row_index 5`

Ciktilar:
- Run ID: `20260306_231713_b9ad0c`
- `tables/plans.csv`
- `tables/plans.json`
- Toplam plan: 9

Ornek sonuc:
- approved_count: 9
- best_plan_id: `20260306_231713_b9ad0c_demo_3_conservative`

---

## Hafta 7 - Safety validator (feasibility + bootstrap CI)
Eklenen dosyalar:
- `src/credit_coach/safety/feasibility.py`
- `src/credit_coach/safety/statistical.py`
- `src/credit_coach/safety/validator.py`
- `src/credit_coach/safety/__init__.py`

Calisma sonucu:
- Recourse run icinde tum planlar safety gate'den gecirildi.
- `plans.csv` icinde `ci_low`, `ci_high`, `risk_margin`, `status` alanlari dolu.

Test:
- `tests/test_validator_ci.py` eklendi ve gecti.

---

## Hafta 8 - Macro stress ve shock reliability
Eklenen dosyalar:
- `src/credit_coach/macro/sources.py`
- `src/credit_coach/macro/stress_index.py`
- `src/credit_coach/macro/events.py`
- `src/credit_coach/macro/impact.py`
- `src/credit_coach/macro/shock_scenarios.py`
- `src/credit_coach/macro/reliability.py`
- `src/credit_coach/macro/shock_sim.py`
- `src/credit_coach/macro/drift_detect.py`
- `src/credit_coach/cli/run_shock.py`

Calistirilan komut:
- `python -m credit_coach.cli.run_shock --macro_config configs/macro.yaml --model_config configs/model.yaml`

Cikti:
- Run ID: `20260306_231720_b6d481`
- `tables/shock_reliability.csv`

Metrikler:
- plan_count: 9
- avg_reliability: 1.0
- min_reliability: 1.0

---

## Hafta 9 - Benchmark ve fairness
Eklenen dosyalar:
- `src/credit_coach/evaluation/bootstrap.py`
- `src/credit_coach/evaluation/metrics.py`
- `src/credit_coach/evaluation/fairness.py`
- `src/credit_coach/evaluation/tables.py`
- `src/credit_coach/evaluation/plots.py`
- `src/credit_coach/cli/run_benchmark.py`
- `src/credit_coach/cli/run_fairness.py`

Calistirilan komutlar:
- `python -m credit_coach.cli.run_benchmark --model_config configs/model.yaml`
- `python -m credit_coach.cli.run_fairness --base_config configs/default.yaml --model_config configs/model.yaml --group_feature home_ownership`

Ciktilar:
- Benchmark Run ID: `20260306_231720_69ab70`
- Fairness Run ID: `20260306_231724_a7f0bf`
- `tables/benchmark_comparison.csv`
- `tables/fairness_report.csv`

Metrikler:
- our_validity: 1.0
- baseline_validity: 1.0
- approval_gap: 0.0799

Test:
- `tests/test_metrics.py` eklendi ve gecti.

---

## Hafta 10 - Weekly coaching loop
Eklenen dosyalar:
- `src/credit_coach/coaching/progress.py`
- `src/credit_coach/coaching/reviewer.py`
- `src/credit_coach/coaching/messaging.py`
- `src/credit_coach/coaching/loop.py`
- `src/credit_coach/coaching/__init__.py`
- `src/credit_coach/cli/run_coaching.py`

Calistirilan komut:
- `python -m credit_coach.cli.run_coaching --weeks 4 --coaching_config configs/coaching.yaml --model_config configs/model.yaml`

Cikti:
- Run ID: `20260306_231728_8b4485`
- `tables/weekly_coaching.csv`

Metrikler:
- weeks: 4
- replan_count: 3
- final_pd: 0.0

Test:
- `tests/test_coaching_progress.py` eklendi ve gecti.

---

## Hafta 11 - Retraining governance ve rapor
Eklenen dosyalar:
- `src/credit_coach/retraining/scheduler.py`
- `src/credit_coach/retraining/data_window.py`
- `src/credit_coach/retraining/train_job.py`
- `src/credit_coach/retraining/model_selection.py`
- `src/credit_coach/retraining/governance.py`
- `src/credit_coach/retraining/__init__.py`
- `src/credit_coach/cli/run_retrain.py`
- `src/credit_coach/cli/run_governance_report.py`

Calistirilan komutlar:
- `python -m credit_coach.cli.run_retrain --base_config configs/default.yaml --model_config configs/model.yaml --governance_config configs/governance.yaml`
- `python -m credit_coach.cli.run_governance_report`

Ciktilar:
- Retrain Run ID: `20260306_231734_990ea5`
- Governance report Run ID: `20260306_231738_b40d0b`
- `tables/governance_decision.json`
- `tables/governance_report.csv`

Metrikler:
- governance status: PASS
- reason_count: 0
- challenger_auc: 0.9571

---

## Hafta 12 - Final smoke, paket kontrolu ve test
Eklenen dosyalar (demo/urun katmani temel iskelet):
- `src/credit_coach/app/state.py`
- `src/credit_coach/app/components.py`
- `src/credit_coach/app/streamlit_app.py`
- `src/credit_coach/app/__init__.py`
- `src/credit_coach/api/schemas.py`
- `src/credit_coach/api/auth.py`
- `src/credit_coach/api/main.py`
- `src/credit_coach/api/__init__.py`
- `src/credit_coach/policy/engine.py`
- `src/credit_coach/portfolio/impact.py`

Final kontrol komutlari:
1. `cd credit-coach && pytest -q`
2. Artifact varlik kontrol scripti (hafta bazli dosya varligi)

Sonuc:
- Pytest: `37 passed`
- Artifact varlik kontrolu:
  - week2 parquet: true
  - week3 model latest: true
  - week4 local reasons: true
  - week6/7 plans: true
  - week8 shock: true
  - week9 benchmark/fairness: true
  - week10 coaching: true
  - week11 governance decision/report: true

---

## 3) Eklenen test dosyalari
- `tests/test_data_pipeline.py`
- `tests/test_model_pipeline.py`
- `tests/test_rex_constraints.py`
- `tests/test_validator_ci.py`
- `tests/test_metrics.py`
- `tests/test_coaching_progress.py`

Toplam test sonucu:
- `37 passed, 1 warning`

---

## 4) Son durum ozeti
Bu rapor kapsaminda 12 haftalik planin tum adimlari icin:
1. Kod modulleri eklendi/guncellendi.
2. Haftalik CLI akislari calistirildi.
3. Ciktilar artifact olarak uretildi.
4. Testler genisletildi ve tumu gecti.

Uretilen tum kritik ciktilar:
- processed dataset
- trained+calibrated model bundle
- local explanations
- causal graph
- 9 plan + safety status
- shock reliability
- benchmark + fairness raporu
- weekly coaching loop
- retraining governance karari + governance report

Ek teknik iyilestirme:
- `src/credit_coach/utils/run_context.py` guncellendi.
- `run_id` formatina 6 haneli `nonce` eklendi.
- Ayni saniyede paralel calisan islerde run_id cakisma riski giderildi.
