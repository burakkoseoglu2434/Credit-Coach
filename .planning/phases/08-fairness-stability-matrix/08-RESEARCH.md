# Phase 8: Fairness Stability Matrix - Research

**Researched:** 2026-03-14
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so seeded fairness behavior becomes deterministic, localizable, and actionable across suite, challenger, and smoke workflows without losing lift or reliability signal?

## Executive Summary

The repo already contains most of the raw ingredients for Phase 8. `run_batch_recourse_eval.py` produces single-run fairness deltas, high-stress comparisons, and a first-pass `fairness_failure_breakdown.csv`. `run_phase_experiment_suite.py` already repeats the batch runner across seeds and writes `phase_scale_seed_summary.csv` plus `phase_scale_aggregate.json`. `run_production_smoke.py` already consumes artifact packs and turns them into gate rows. `run_model_challenger_matrix.py` already ranks variants against KPI thresholds.

The missing piece is not a brand-new fairness engine. The missing piece is a shared decision contract that sits between these runners and the existing artifacts:

- separate lift, reliability, and fairness pass semantics instead of folding everything into one `all_pass`
- aggregate seed failures into deterministic `GO | LIMITED_GO | NO_GO` outcomes
- localize fairness failures into a canonical segment catalog with source-aware explanations
- preserve traceability when fairness guard or quota-like controls change which candidates survive

Phase 8 should therefore be planned as contract hardening plus evidence packaging, not as a model rewrite.

## Existing Assets We Can Reuse

### Fairness helpers already in place

- `credit-coach/src/credit_coach/evaluation/fairness.py`
  - `build_composite_group(...)`
  - `compute_multi_segment_fairness(...)`
  - `compute_fairness_bundle(...)`
  - `build_fairness_stress_matrix(...)`
- These give us a natural home for canonical segment keys, fail-reason helpers, and rollups shared by more than one runner.

### Single-run diagnostics already emitted

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - writes `batch_fairness_change.csv`
  - writes `batch_fairness_stress_compare.csv`
  - writes `fairness_failure_breakdown.csv`
  - already tracks `risk_band`, `income_band`, `best_source`, `fairness_guard_demoted`, and fairness guard stop reasons
- The existing `_build_fairness_failure_breakdown(...)` function is the best starting point for Phase 8 localization work.

### Seeded suite scaffold already exists

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - repeats seeded runs
  - writes `phase_scale_seed_summary.csv`
  - writes `phase_scale_aggregate.json`
  - already has `_kpi_checks(...)`
- Today it only reports `all_pass` plus a string list of failed checks. Phase 8 needs it to emit structured lift, reliability, and fairness seed status plus aggregate release metrics.

### Downstream consumers already exist

- `credit-coach/src/credit_coach/cli/run_production_smoke.py`
  - produces stable gate rows and `kpi_snapshot.json`
  - today only emits binary `overall_status`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already performs threshold-aware variant selection
  - today optimizes around mean metrics and gate violation score, not pilot-only semantics

## Gaps Phase 8 Must Close

### 1. Shared release decision logic is missing

The repo has KPI threshold loading in `credit_coach/ops/kpi_contract.py`, but no shared helper that says:

- which metrics define fairness seed pass
- how many fairness seed passes are required for `GO`
- when localization is strong enough for `LIMITED_GO`
- how `LIMITED_GO` differs from `NO_GO` operationally

Without that helper, suite, challenger, and smoke will drift.

### 2. Seed summaries are too coarse

`phase_scale_seed_summary.csv` currently tells us whether an entire seed passed all checks, but it does not separate:

- `lift_pass`
- `reliability_pass`
- `fairness_seed_pass`
- `primary_fail_reason`
- `worst_fairness_gap`

That makes seeded fairness instability visible only as noise, not as a decision-ready contract.

### 3. Localization exists per batch, not per phase contract

The current `fairness_failure_breakdown.csv` is useful, but Phase 8 needs a stable contract that always exposes:

- `seed x segment`
- `segment x candidate source`
- `high-stress scenario x segment`
- `seed x primary_fail_reason`
- `risk band x source` rollup

It also needs `dominant_fail_segment_key` from a unified canonical segment catalog plus a companion `dominant_fail_candidate_source` field when possible.

### 4. Fairness control traceability is not yet decision-grade

`run_batch_recourse_eval.py` already performs fairness guard demotions and quota-like selection, but the seeded release evidence does not yet make it easy to answer:

- which control fired
- which segment or source it protected
- what lift floor prevented further demotion
- whether a `LIMITED_GO` result came from localized instability or from hidden control side effects

That comparability gap is exactly what `FAIR-03` is about.

## Recommended Architecture

### A. Shared release helper in `credit_coach/ops`

Introduce a small shared helper module such as `credit_coach/ops/release_decision.py` that owns:

- fairness seed pass evaluation from primary and guardrail metrics
- lift and reliability precedence rules
- aggregate seed counting
- `evaluate_release_decision(metrics) -> GO | LIMITED_GO | NO_GO`
- `LIMITED_GO` operational package builders
- rollback condition builders

Why `ops/` instead of `evaluation/`:

- the rules are operational release semantics, not just metric math
- smoke and challenger need the same behavior even when they are not computing raw fairness bundles directly

### B. Canonical segment and breakdown helpers in `evaluation/fairness.py`

Extend fairness helpers so one shared implementation can build:

- canonical segment keys from `risk_band`, `income_band` or quantile, and `stress_band`
- dominant fail segment summaries
- fail-reason concentration summaries
- risk-band by source rollups

This keeps localization math close to the existing fairness utilities and avoids copy-pasting segment logic into each CLI runner.

### C. Keep one canonical breakdown CSV, not many loosely related tables

To avoid artifact sprawl, the best fit is a single canonical `fairness_failure_breakdown.csv` with a stable schema and a `breakdown_type` column. That lets one file carry:

- `seed_segment`
- `segment_source`
- `high_stress_segment`
- `seed_primary_fail_reason`
- `risk_band_source_rollup`

The canonical artifact stays CSV-first for automation, while different views remain easy to filter.

### D. Emit derived decision artifacts only after localization exists

`release_decision.json`, `pilot_guardrails.json`, `rollback_conditions.json`, and `release_review_summary.md` should be generated only after the seeded localization metrics are available. That means:

- Phase slice 1: define seed contract and aggregate metrics
- Phase slice 2: define localization outputs
- Phase slice 3: emit deterministic decisions and pilot-only evidence from those inputs

## Artifact Contract Recommended For Phase 8

| Artifact | Producer | Why it matters |
|----------|----------|----------------|
| `phase_scale_seed_summary.csv` | `run_phase_experiment_suite.py` | Seed-level contract for lift, reliability, fairness pass/fail, and worst gaps |
| `phase_scale_aggregate.json` | `run_phase_experiment_suite.py` | Aggregate counts such as fairness seed pass count, total seeds, and worst observed gaps |
| `fairness_failure_breakdown.csv` | batch runner plus seeded suite rollup | Canonical localization evidence across required breakdown types |
| `release_decision.json` | shared helper invoked by suite/smoke/challenger | Machine-readable release classification |
| `pilot_guardrails.json` | shared helper when `LIMITED_GO` | Makes pilot restrictions explicit |
| `rollback_conditions.json` | shared helper when `LIMITED_GO` | Stable rollback triggers for operations |
| `release_review_summary.md` | derived from canonical artifacts | Human-readable release review summary |

## Implementation Strategy By Plan Slice

### Slice 08-01: Shared seed contract and aggregate artifacts

Focus:

- split current `all_pass` into lift, reliability, and fairness components
- define fairness seed pass around:
  - `equalized_odds_gap_delta`
  - `high_stress_fairness_gap_after`
  - `recourse_success_gap`
- extend seeded suite outputs with pass counts and worst-gap fields

Primary files:

- `credit-coach/src/credit_coach/ops/release_decision.py`
- `credit-coach/src/credit_coach/ops/__init__.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach/tests/test_release_decision.py`

### Slice 08-02: Canonical localization and breakdown rollups

Focus:

- upgrade breakdown helpers to emit canonical segment keys
- preserve candidate source as a companion field where possible
- aggregate per-seed localization into one stable breakdown artifact

Primary files:

- `credit-coach/src/credit_coach/evaluation/fairness.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`
- `credit-coach/tests/test_recourse_fairness_metrics.py`

### Slice 08-03: Deterministic release semantics and control traceability

Focus:

- emit `GO | LIMITED_GO | NO_GO`
- make `LIMITED_GO` non-passing in smoke but pilot-eligible
- keep challenger promotion locked behind `GO`
- expose fairness guard and quota-style interventions so lift remains comparable

Primary files:

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
- `credit-coach/src/credit_coach/cli/run_production_smoke.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/tests/test_production_smoke.py`
- `credit-coach/tests/test_challenger_matrix_selection.py`

## Key Risks And How To Plan Around Them

### Risk: mean metrics can hide the single bad seed that matters

Planning implication:

- always carry `worst_*` fields and fairness seed pass counts
- do not let aggregate means drive release classification by themselves

### Risk: localization can drift across runners

Planning implication:

- centralize canonical segment construction in shared helpers
- do not let smoke or challenger invent their own segment labels

### Risk: fairness controls can silently trade away business value

Planning implication:

- whenever fairness guard or quota-like logic changes candidate outcomes, keep lift and reliability floor checks close by
- expose stop reasons and demotion counts in comparable artifacts

### Risk: `LIMITED_GO` can accidentally behave like a silent pass

Planning implication:

- separate `release_decision` from `smoke_pass`
- add explicit `pilot_eligible`, rollout cap, monitoring, and rollback metadata

## Validation Architecture

### Existing test infrastructure is sufficient

- Framework: `pytest` via `credit-coach/pyproject.toml`
- Existing contract-style tests already cover:
  - phase suite contract behavior
  - smoke gate-row behavior
  - challenger selection ranking
  - fairness breakdown builders

### Recommended sampling strategy

- After shared helper or runner changes: run targeted contract tests
- After each wave: run the full Phase 8 target suite
- Before execution completion: verify all Phase 8 contract tests are green together

### Minimum automated coverage per slice

- Slice 08-01:
  - helper tests for `GO`, `LIMITED_GO`, and `NO_GO`
  - suite tests for seed pass counting and aggregate fields
- Slice 08-02:
  - breakdown tests for canonical segment key, fail reason, and source rollups
  - suite tests for merged seeded breakdown artifacts
- Slice 08-03:
  - smoke tests for `release_decision`, `smoke_pass`, `pilot_eligible`
  - challenger tests that `LIMITED_GO` cannot auto-promote a champion
  - traceability tests for fairness guard or quota-side evidence

### Phase 8 quick/full commands

- Quick command:
  - `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_batch_candidate_diversity.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py`
- Full command:
  - `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_batch_candidate_diversity.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py tests/test_recourse_fairness_metrics.py`

## Sources

- `.planning/phases/08-fairness-stability-matrix/08-CONTEXT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/research/SUMMARY.md`
- `credit-coach/src/credit_coach/evaluation/fairness.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
- `credit-coach/src/credit_coach/cli/run_production_smoke.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`
- `credit-coach/tests/test_challenger_matrix_selection.py`
- `credit-coach/tests/test_production_smoke.py`

---
*Phase: 08-fairness-stability-matrix*
*Research completed: 2026-03-14*
