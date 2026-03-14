# Retry Execution Report (2026-03-09)

## Scope
This retry run completed the remaining phase executions end-to-end:
1. 1000-customer x 5-seed batch gate run with current `recourse_phaseb_hybrid_v2` config.
2. Challenger matrix rerun (`4 variants x 5 seeds`) with latency gate alignment fix.
3. Full-contract seed-level gate check for top challenger variants.

## Code Changes Applied

### 1) Fairness-cap boost instrumentation in batch recourse
- File: `src/credit_coach/cli/run_batch_recourse_eval.py`
- Added `_apply_fairness_segment_cap_boost(...)`.
- Added row-level diagnostics fields:
  - `fairness_group`
  - `fairness_cap_boost_applied`
  - `fairness_cap_boost_factor`
- Added summary metrics:
  - `fairness_cap_boost_applied_rate`
  - `fairness_cap_boost_factor_avg`

### 2) Config updates for fairness balancing and segment-cap boost
- File: `configs/experiments/recourse_phaseb_hybrid_v2.yaml`
- Updated fairness balancing parameters.
- Added `fairness.segment_cap_boost` block.

### 3) Challenger latency gate alignment fix
- File: `src/credit_coach/cli/run_model_challenger_matrix.py`
- Challenger evaluation now uses sync latency (`sync_latency_p95/p99`) when available, consistent with production smoke gate behavior.
- Preserved raw latency fields in challenger output:
  - `latency_p95_ms_raw`
  - `latency_p99_ms_raw`
  - `latency_mode`

### 4) Tests
- File: `tests/test_batch_candidate_diversity.py`
- Added tests for fairness segment-cap boost helper.
- Test status: PASS (`23 passed` for target suite).

## Batch 1000 x 5 Seeds (Current Profile)

Run IDs:
- seed 42: `20260309_134635_48eddb_16b5b1`
- seed 43: `20260309_134537_e9ba0e_0f252a`
- seed 44: `20260309_134707_3661fb_5f3556`
- seed 45: `20260309_134745_ed42c3_e8dc1f`
- seed 46: `20260309_134816_6c72c9_1f86fd`

Aggregate (means):
- `denied_to_approved_lift`: **0.1717** (PASS)
- `denied_high_risk_lift`: **0.1823** (PASS)
- `sync_latency_p95_ms`: **450** (PASS)
- `sync_latency_p99_ms`: **450** (PASS)
- `error_rate`: **0.0** (PASS)
- `recourse_success_gap`: **0.1223** (FAIL vs `<=0.10`)
- `equalized_odds_gap_delta`: **0.0597** (FAIL vs `<=0.01`)

Full contract pass count:
- **0 / 5 (NO_GO)**

Primary fail drivers:
- `equalized_odds_gap_delta` (all 5 seeds)
- Fairness gap / recourse success gap in subset of seeds.

Saved summary:
- `artifacts/runs/20260309_5seed_gate_summary.csv`

## Challenger Matrix (Retry Rerun)

Run ID:
- `20260309_141936_25be6a_6c6ffe`

Ranked variants (challenger gate set):
1. `logistic_sigmoid` (gate_all_pass: true)
2. `xgboost_monotonic_sigmoid` (gate_all_pass: true)
3. `control_logistic_isotonic` (fail)
4. `xgboost_monotonic_isotonic` (fail)

Decision artifact:
- `artifacts/runs/20260309_141936_25be6a_6c6ffe/tables/challenger_matrix_decision.json`

Important note:
- Challenger internal gate set is narrower than full production contract.
- It does not fully enforce all fairness-delta constraints used in full release smoke.

## Full-Contract Seed Check for Top Challenger Variants

Saved file:
- `artifacts/runs/20260309_challenger_fullcontract_seed_gates.csv`

Results:
- `logistic_sigmoid`: **1 / 5 PASS**
- `xgboost_monotonic_sigmoid`: **0 / 5 PASS**

Dominant fail reason remains:
- `equalized_odds_gap_delta > 0.01` across most seeds.

## Concrete Conclusion
Current system now reliably achieves lift and latency targets, but remains **release-blocked by fairness-delta stability** under full KPI contract at 5-seed scale.

## Next Execution Backlog (P0)
1. Add **fairness-delta-aware denied objective** directly to generator/planner score (include equalized-odds delta proxy term, not only approval-gap penalty).
2. Add **seed-robust fairness gate in optimization loop** (early stopping or candidate rejection when fairness delta trend worsens).
3. Add **group-conditional candidate budget balancing** to avoid one-group over-conversion causing EO-delta spikes.
4. Promote challenger selection to use **full contract scoring** (include `equalized_odds_gap_delta` and `recourse_success_gap`), not reduced gate set.
5. Re-run `1000 x 5` with mandatory full-contract PASS criteria.
