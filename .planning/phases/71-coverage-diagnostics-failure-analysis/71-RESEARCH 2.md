# Phase 71: Coverage Diagnostics & Failure Analysis — Research

**Researched:** 2026-04-18  
**Purpose:** capture the minimum operational knowledge needed to explain the `~97%` empty-state / limited-mode outcome in W2a without changing shipped gating, selection, or artifact contracts.

## Primary Evidence Inputs (W2a)

Canonical W2a evaluation directory (current baseline for Phase 71):
- `credit-coach/artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/W2a_large_n3000_seed42/`

Key files available in that directory:
- `customer_level_analysis.csv` — row-level spine table (already contains recoverability, gate outputs, and path/movement proxies)
- `path_groupings.jsonl` — path-level evidence (latent path types + action families)
- `candidate_plans.jsonl` — candidate plan evidence (large; stream-only for joins)
- `selected_plans.jsonl` — selected-plan metadata (note: currently does not carry selected action families)
- `cohort_metrics.json` — aggregate metrics + trust counters

Phase 71 should treat `customer_level_analysis.csv` as the *primary* diagnostic spine and only join heavier artifacts when needed for mismatch analysis.

## What “coverage loss” means in this system

Phase 71 needs to decompose customers into buckets that explain why the final surfaced output is empty/limited, while respecting the existing stable runtime vocabulary:
- keep shipped gate codes stable (e.g., `RECOVERABLE_FULL_MODE`, `NOT_RECOVERABLE_LIMITED_MODE`)
- publish a *derived* coverage-loss taxonomy as additive diagnostics

Operationally, the output collapse observed in W2a is consistent with:
- recoverability + gate routing pushing most customers into limited mode (`recourse_mode=limited`)
- limited-mode behavior intentionally rewriting selected truth to empty-state, which zeroes selected movement-style fields
- latent richness still present upstream (path diversity metrics remain high even when surfaced output is empty)

## Evidence already present in `customer_level_analysis.csv`

Columns Phase 71 can use without parsing JSONL artifacts:
- segmentation: `recoverability_bucket` (`near_threshold`, `mid_risk`, `structural_limited`)
- gate and surface outcomes: `recourse_mode`, `recommendation_mode`, `selected_recommendation_source`, `empty_state_flag`, `zero_action_flag`
- latent structure proxies: `has_valid_path_flag`, `has_rankable_path_flag`, `path_count`, `rankable_path_count`, `multi_path_flag`, `action_categories_json`, `unique_action_count_per_customer`
- latent movement / threshold proxies (pre-gate maxima): `movement_potential`, `max_gap_closure_rate`, `best_reachable_pd`, `path_reaches_threshold_flag`
- guardrails: `selected_invalid_winner_flag`, `selected_surface_drift_flag`, `operator_packet_contradiction_flag`
- reason-code primitives: `recoverability_signal_reason_codes_json`, `recoverable_reason_codes_json`, `recourse_gate_reason_codes_json`, `movement_rank_reason_codes_json`

Implication: Phase 71 can produce a first-pass empty-state decomposition using only this CSV (fast and low risk), then add mismatch analysis as a second layer.

## Latent vs surfaced mismatch (why JSONL parsing may be needed)

To quantify “latent action diversity vs surfaced action diversity” and identify where selection collapses to empty-state despite latent richness:
- latent action families are already summarized in `customer_level_analysis.csv` (e.g., `action_categories_json`)
- surfaced/selected action family is not directly recorded in the CSV
- `selected_plans.jsonl` currently carries IDs and outcome metadata but not action family payloads

Therefore, mismatch analysis likely needs a join:
- `customer_level_analysis.csv.selected_plan_id` → stream `candidate_plans.jsonl` to find the matching plan record and extract its action-family fields

This must be done streaming (file is large) and should be optional in the diagnostic tool so Phase 71 can still run quickly.

## Safe integration points (no semantics change)

Existing evaluation runner:
- `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py`
  - already writes the Phase 71 spine (`customer_level_analysis.csv`)
  - has a clear end-of-run seam to append additive artifacts without changing selection semantics

Existing gate seam:
- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `_attach_recoverability_signal_to_roadmap(...)` and `_apply_recourse_gate_to_roadmap(...)` establish why limited-mode customers lose selected truth
  - Phase 71 must not change these semantics; only observe and explain them

## Artifact strategy (additive, standalone)

Phase 71 should write a standalone diagnostic artifact family (names locked in Phase 71 context):
- `coverage_diagnostic_summary.json`
- `coverage_diagnostic_customer_breakdown.csv`
- `coverage_reason_frequency.csv`
- `empty_state_decomposition.json`
- `latent_vs_surfaced_mismatch.csv` (optional; requires mismatch join)
- `coverage_diagnostic_report.md`

Recommended placement:
- under the evaluation run directory (e.g., `.../W2a_large_n3000_seed42/coverage_diagnostics/`) so the artifacts travel with the run
- ensure generation is idempotent and deterministic for the same inputs

## Control anchor (taxonomy stability)

Phase 71 should run diagnostics on W2a plus one control anchor to ensure the taxonomy is not a one-run artifact. Lowest-friction anchors available in the workspace:
- `credit-coach/artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42/` (same runtime family), or
- Phase 68 canonical: `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42/`

## Risks and guardrails

- Do not redefine or replace `customer_level_analysis.csv`; keep Phase 71 output additive.
- Do not invent new runtime gate reason codes in Phase 71; publish a derived diagnostic taxonomy only.
- Clearly distinguish:
  - “structurally limited” (no credible latent value)
  - “policy-suppressed / potentially useful” (latent value exists but is suppressed by gate/surface policy)
- Keep thresholds explicit (e.g., a documented epsilon for “movement-positive” and “non-trivial threshold signal”).

---

## RESEARCH COMPLETE

