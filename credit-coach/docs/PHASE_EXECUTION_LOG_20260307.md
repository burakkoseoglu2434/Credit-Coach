# Phase Execution Log - 2026-03-07

## Scope
- Focused on recourse production hardening bottlenecks:
  - latency outliers (`p95/p99`)
  - denied-to-approved conversion lift
  - fairness delta and smoke gate compliance

## Code Changes

### 1) DiCE timeout capability (configurable)
- Added configurable `timeout_ms` support to DiCE generation.
- Timeout logic is opt-in (`0` means disabled), and reported via telemetry fallback reason `timeout`.
- Files:
  - `src/credit_coach/recourse/dice_baseline.py`
  - `src/credit_coach/cli/run_batch_recourse_eval.py`
  - `src/credit_coach/cli/run_recourse.py`

### 2) Recourse default profile tuning
- Updated default recourse profile to a stable KPI-passing operating point:
  - `dice.total_cfs: 2`
  - `search_budget.denied_dice_max_customers: 30`
  - `dice.timeout_ms: 0` (disabled by default)
- File:
  - `configs/recourse.yaml`

### 3) Test coverage expansion
- Added timeout fallback unit test for DiCE adapter hardening.
- File:
  - `tests/test_dice_adapter_hardening.py`

## Validation
- Unit/integration tests:
  - `pytest -q` -> `86 passed`

## Batch Experiment Summary (1000 customers)

| Run ID | Profile | denied_lift | p95(ms) | p99(ms) | eq_odds_delta | Smoke |
|---|---|---:|---:|---:|---:|---|
| `20260307_133329_9cc9d5_72efdb` | q50/cfs3, workers=5 | 0.1477 | 448.51 | 2697.54 | +0.01954 | NO_GO |
| `20260307_135256_ce933f_bc0337` | q50/cfs3, workers=1 | 0.1308 | 31.51 | 218.45 | +0.04201 | NO_GO |
| `20260307_135350_70b2bf_f25f47` | q30/cfs2, workers=1 | 0.0549 | 20.68 | 207.23 | -0.01009 | GO |
| `20260307_135515_70b2bf_c67b87` | q30/cfs2 (default), workers=1 | 0.0549 | 16.95 | 193.27 | -0.01009 | GO |

Notes:
- `eq_odds_delta` shown as `after - before`.
- Smoke threshold check is `equalized_odds_gap_delta <= 0.01`; negative deltas pass.

## Final Smoke Gate Output
- Batch run used for final smoke:
  - `artifacts/runs/20260307_135515_70b2bf_c67b87/tables/batch_summary.json`
- Smoke run:
  - `artifacts/runs/20260307_135553_fafb88_d344bd/tables/production_smoke_report.csv`
- Final status: `GO` (`G0..G5 PASS`)

## Recommended Production CLI (current profile)
```bash
TQDM_DISABLE=1 python -m credit_coach.cli.run_batch_recourse_eval \
  --n_customers 1000 \
  --sample_seed 42 \
  --log_every 100 \
  --n_workers 1 \
  --base_config configs/default.yaml \
  --model_config configs/model.yaml \
  --recourse_config configs/recourse.yaml \
  --causality_config configs/causality.yaml \
  --safety_config configs/safety.yaml \
  --macro_config configs/macro.yaml
```
