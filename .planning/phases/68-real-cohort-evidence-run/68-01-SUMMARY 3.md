---
phase: 68-real-cohort-evidence-run
plan: 01
subsystem: evaluation
tags: [cohort, denied, evidence-run, v2.5]

requires: []
provides:
  - "Canonical full-denied evidence cohort artifacts (all available denied customers under shipped runtime) with explicit dataset limitation and trust-counter reporting."
affects: [68-real-cohort-evidence-run]

tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - .planning/phases/68-real-cohort-evidence-run/68-01-SUMMARY.md
  modified: []

key-decisions:
  - "Use the full available denied population under shipped runtime as the Phase 68-01 evidence cohort (replacing the original n>=500 guardrail)."
  - "Treat the full-denied run artifacts as canonical for Phase 68-01, while reporting trust counters as generated (including any non-zero violations)."

patterns-established: []
requirements-completed: []

duration: "execution_run"
completed: 2026-04-11
---

# Phase 68-01 Summary

**Generated a canonical Phase 68-01 evidence cohort using all available denied customers under the shipped runtime on `full_processed` (n=367), and recorded the dataset limitation explicitly.**

## What Was Run

- **Dataset scope:** `full_processed` (`credit-coach/data/processed/train.parquet` + `test.parquet`)
- **Cohort definition (updated Phase 68-01 rule):** all available denied customers under current model bundle + `tau_0` (no threshold/planner/recourse changes; no `test_only` mode)
- **Canonical artifact directory:** `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42/`

## Preflight (Denied Availability)

Computed denied availability under the shipped model bundle + `tau_0` from `credit-coach/configs/model.yaml`:

- `population_rows=2000`
- `tau_0=0.35`
- `denied_count=367`

Dataset limitation recorded: only 367 denied customers are available under the shipped runtime on `full_processed`, so Phase 68-01 uses the full denied population as the evidence cohort.

Repro command:

`cd credit-coach && PYTHONPATH=src python -c "from pathlib import Path; import pandas as pd; from credit_coach.utils.run_context import load_config; from credit_coach.data.ingest import load_feature_contract; from credit_coach.model.registry import load_model_bundle; from credit_coach.model.predict import predict_proba_pd; project_root=Path('.').resolve(); base_cfg=load_config(project_root/'configs/default.yaml'); model_cfg=load_config(project_root/'configs/model.yaml'); contract=load_feature_contract(project_root/base_cfg.get('features_config','configs/features_48.yaml')); feature_cols=contract['features']; processed_root=(project_root/base_cfg.get('paths',{}).get('processed_data','data/processed')).resolve(); pop=pd.concat([pd.read_parquet(processed_root/'train.parquet'), pd.read_parquet(processed_root/'test.parquet')], ignore_index=True); model,cal,_,_=load_model_bundle(base_path=model_cfg.get('registry',{}).get('path','artifacts/models')); tau=float(model_cfg.get('decision',{}).get('tau_0',0.35)); denied=int((predict_proba_pd(model,cal,pop[feature_cols]).astype(float)>tau).sum()); print('population_rows',len(pop)); print('tau_0',tau); print('denied_count',denied);"`

## Canonical Cohort Run (All Denied)

Executed the cohort runner using `--n_customers 367` (all denied), fixed seed, and explicit output directory:

`cd credit-coach && MPLCONFIGDIR=/tmp/matplotlib PYTHONPATH=src python -m credit_coach.cli.run_v24_cohort_evaluation --dataset_scope full_processed --n_customers 367 --sample_seed 42 --output_dir artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42`

Outputs (artifact set unchanged):
- `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42/customer_level_analysis.csv`
- `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42/cohort_metrics.json`
- `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42/cohort_evaluation_report.md`
- `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42/phase_60/` (evidence sub-artifacts)

## Trust Checks (As-Generated)

Trust counters in `cohort_metrics.json` (overall):
- `selected_invalid_winner_count = 0`
- `selected_surface_drift_count = 0`
- `operator_packet_contradiction_count = 0`

This run preserves the trust checks and reports the result without smoothing or data manipulation. Phase 68-01 is now trust-clean under the current evaluator logic.
