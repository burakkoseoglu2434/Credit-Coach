# Batch 1000 KPI Delta Report (2026-03-08)

New run:
- `20260308_063014_9ede50_c13432`

Baseline run:
- `20260307_022407_09670e_e8ee2f`

Command:
- `python -m credit_coach.cli.run_batch_recourse_eval --n_customers 1000 --sample_seed 42 --n_workers 5 ...`

Output tables:
- `artifacts/runs/20260308_063014_9ede50_c13432/tables/batch_summary.json`
- `artifacts/runs/20260308_063014_9ede50_c13432/tables/kpi_delta_vs_20260307_022407_09670e_e8ee2f.csv`

## New run snapshot
- denied_to_approved_lift: `0.0464`
- denied_high_risk_lift: `0.0000`
- denied_reliability_violation_rate: `1.0000`
- denied_ci_violation_rate: `0.0088`
- dice_success_rate: `0.0260`
- best_source_rule_rate: `0.2210`
- candidate_pool_diversity_index: `0.0936`
- candidate_source_entropy: `0.1749`
- fairness_approval_gap_after: `0.0934`
- fairness_equalized_odds_gap_after: `0.1065`
- latency_p95_ms: `861.78`
- latency_p99_ms: `8510.22`

## Delta highlights (new - old)
- denied_to_approved_lift: `-0.8987`
- approval_rate_lift: `-0.2130`
- avg_pd_reduction: `-0.1764`
- dice_success_rate: `-0.9740`
- latency_avg_ms: `-379.70`
- latency_p95_ms: `+252.86`
- fairness_approval_gap_after: `+0.0856`
- fairness_equalized_odds_gap_after: `+0.0324`

## Quick interpretation
- Runtime total ciddi iyilesti (`elapsed_total_s` 666.5s -> 57.7s), fakat etkinlik KPI'lari (lift, pd_reduction) belirgin dustu.
- High-risk lift halen `0.0`.
- CI ihlali ciddi azalmis olsa da reliability ihlali halen cok yuksek.
