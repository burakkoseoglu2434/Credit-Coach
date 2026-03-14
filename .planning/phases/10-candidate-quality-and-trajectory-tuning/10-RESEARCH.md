# Phase 10: Candidate Quality and Trajectory Tuning - Research

**Researched:** 2026-03-15
**Status:** Ready for replanning
**Confidence:** HIGH

## Planning Question

What has to change so existing batch-level candidate diversity, source entropy, and denied high-risk trajectory signals become seeded milestone evidence that explains which generator or policy shifts helped or harmed KPI outcomes?

## Planning Assumption

This research pass is the forced re-research step after `10-CONTEXT.md` captured the user decisions that planning had previously lacked. The authoritative inputs for this pass are now:

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/10-candidate-quality-and-trajectory-tuning/10-CONTEXT.md`
- Phase 8 and Phase 9 outputs
- current CLI and test code under `credit-coach/src/credit_coach/` and `credit-coach/tests/`

That is sufficient because `CAND-01`, `CAND-02`, and `CAND-03` are concrete, the user has now locked the remaining interpretation decisions, and the repo already contains most of the raw instrumentation needed for this phase.

## Executive Summary

Phase 10 should not invent a new candidate-generation stack. The repo already computes candidate diversity, candidate source entropy, best-source mix, denied high-risk lift, and high-risk reachability inside batch evaluation. What is missing is the layer that promotes those local metrics into seeded suite evidence, challenger comparisons, and milestone-ready diagnostics under one explicit interpretation contract.

That makes this a promotion and explanation phase, not an algorithm-discovery phase. The main job is to make existing batch metrics durable across seeded runs, tie them to generator and policy provenance, and explain KPI movement in a way that is useful for milestone review. If execution tries to add too many new heuristics at once, it will blur the measurement contract that Phase 8 and Phase 9 just stabilized.

The recommended breakdown is:

- instrument the locked candidate-quality contract in canonical seeded evidence
- harden the existing high-risk phase-1 tuning path with explicit activation and diagnostic semantics
- publish comparative, control-baselined generator and policy impact summaries beside batch KPI artifacts

## Existing Assets We Can Reuse

### Batch evaluation already computes almost the entire Phase 10 raw metric set

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already computes `candidate_pool_diversity_index`
  - already computes `candidate_source_entropy`
  - already writes `best_source_internal_rate`, `best_source_dice_rate`, `best_source_rule_rate`, and `best_source_fallback_rate`
  - already writes companion provenance artifacts such as `denied_candidate_source_breakdown.csv`, `dice_backend_distribution.csv`, and `dice_fallback_distribution.csv`
- `credit-coach/tests/test_batch_candidate_diversity.py`
  - already locks the current diversity helpers and source-entropy behavior

This means `CAND-01` is primarily an aggregation, naming, and artifact-design problem rather than a new metric-invention problem.

### High-risk fast-track behavior already exists

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already exposes `_apply_high_risk_profile(...)`
  - already writes `high_risk_profile_applied_rate`
  - already measures `denied_high_risk_lift`
  - already measures `denied_high_risk_bridge_rate`
  - already measures `denied_high_risk_any_pd_reduction_rate`
  - already measures `high_risk_reachability_rate`
  - already measures `trajectory_partial_progress_rate`
- `credit-coach/tests/test_batch_candidate_diversity.py`
  - already covers high-risk profile activation and guard conditions

This means `CAND-02` should harden and interpret an existing path instead of introducing a second tuning system. The main new decision from context is that `denied_high_risk_lift` is the primary signal, while reachability and partial progress remain supporting signals, and `high_risk_profile_applied_rate >= 0.05` is the threshold for non-anecdotal evidence.

### Suite, challenger, and acceptance layers are now stable enough to extend

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already emits seeded summary CSVs
  - already emits aggregate JSON
  - already writes `kpi_contract_snapshot.json`
  - already writes `milestone_acceptance_summary.json`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already ranks variants using seeded KPI evidence
  - already carries denied high-risk lift and reachability metrics in challenger summaries
  - already computes champion-versus-control deltas that can act as the primary attribution baseline

Phase 10 can therefore reuse the Phase 9 evidence contract instead of building a parallel reporting lane.

## Context-Locked Interpretation Contract

### Candidate-quality evidence is mandatory, but non-blocking

The user locked the canonical seeded candidate-quality fields to:

- `candidate_pool_diversity_index`
- `candidate_source_entropy`
- `best_source_internal_rate`
- `best_source_dice_rate`
- `best_source_rule_rate`
- `best_source_fallback_rate`

These must be visible in seeded evidence, but they must not become release-blocking gates in this phase. The canonical population is `denied`, with `high_risk_denied` kept as a companion view rather than the main interpretation layer.

### High-risk tuning must distinguish real wins from anecdotal wins

The user locked the following interpretation:

- primary tuning metric: `denied_high_risk_lift`
- supporting metrics: `high_risk_reachability_rate`, `trajectory_partial_progress_rate`
- minimum meaningful activation: `high_risk_profile_applied_rate >= 0.05`
- if activation is below threshold, seed direction is unstable, or supporting metrics worsen, the outcome is diagnostic-only

This means Phase 10 is not searching for a new gate. It is building a disciplined evidence policy for whether a tuned high-risk path deserves promotion attention.

### Attribution must be comparative, not causal

The user explicitly rejected causal language. Phase 10 should therefore describe impact as comparative seeded evidence against a primary `control variant` baseline. The output should remain metric-by-metric rather than collapsing into one synthetic score.

The required labels are:

- `helped`
- `harmed`
- `mixed`
- `no_material_change`

and the confidence label is:

- `strong`
- `tentative`

`strong` only applies when repeated seeded evidence exists, the direction is consistent, and the evidence is not degraded.

### Review should explain decisions, not behave like a dashboard

The derived review surface is now explicitly locked to a concise explanation role. It should surface:

- decision
- candidate quality summary
- high-risk tuning summary
- impact attribution summary
- fairness and reliability snapshot
- supporting artifacts

That gives Phase 10 a focused human-review surface without stealing scope from a later operator dashboard phase.

## External Patterns Worth Preserving

### Diverse recourse should stay measurable, not merely anecdotal

The DiCE line of work treats candidate diversity as a first-class property rather than a side effect of search. That supports promoting diversity and source-mix metrics into seeded evidence instead of burying them inside one-off batch summaries.

### Actionability beats aggressive search

Actionable recourse literature consistently favors constrained and feasible actions over superficially strong but unstable recommendations. That supports a Phase 10 design where high-risk fast-track tuning stays bounded by existing fairness and reliability gates rather than becoming an unconditional optimization path.

### Coaching-style systems need explanation, not only scores

Coaching-oriented credit interventions are most useful when they explain which strategy changed the near-term path. That supports generator and policy impact diagnostics as derived artifacts beside KPI snapshots, rather than only as raw numeric deltas.

## Gaps Phase 10 Must Close

### 1. Candidate-quality metrics stop at the batch boundary

Today the repo can measure diversity, entropy, and source mix inside batch evaluation, but seeded suite and milestone evidence do not surface those numbers as stable run-to-run signals under the locked `denied` population contract. As a result, candidate quality exists locally but not at the milestone decision layer.

### 2. High-risk tuning is visible in code but not fully decision-ready

The repo already has opt-in high-risk profile logic and metrics, but seeded evidence does not yet explain:

- how often the profile activated
- whether `denied_high_risk_lift` improved consistently enough to be more than anecdotal
- whether supporting reachability and partial-progress metrics agreed with that improvement
- whether the tuned path stayed inside reliability and fairness guardrails

### 3. Generator and policy impact is still hard to explain

Current outputs can show that KPI values moved, but not yet which source or policy shift helped or harmed them under a comparative, control-baselined interpretation. That keeps `CAND-03` open even though many of the raw ingredients are already present.

### 4. Phase 10 must avoid swallowing Phase 11

It would be easy to turn this phase into a broader release-pack redesign, but telemetry-required production gates and outcome-feedback publication belong to Phase 11. Phase 10 should stay focused on candidate quality, trajectory tuning, and diagnostic explainability inside the existing seeded evidence contract.

## Recommended Architecture

### A. Extend seeded suite artifacts instead of inventing a second evidence lane

Promote batch-level candidate metrics into:

- `phase_scale_seed_summary.csv`
- `phase_scale_aggregate.json`
- `candidate_quality_summary.json`
- `kpi_contract_snapshot.json` supporting-artifact references
- `milestone_acceptance_summary.json` supporting-artifact references

This keeps milestone evidence canonical while avoiding bloated acceptance payloads. The seeded suite should own the canonical `denied` population summary while still linking out to `high_risk_denied` companion evidence.

### B. Treat candidate provenance as machine-readable first

Phase 10 should write canonical companion artifacts such as:

- `candidate_quality_summary.json`
- `candidate_source_breakdown.csv`
- `generator_policy_impact_summary.json`

Human-readable review text can then derive from these artifacts without becoming the source of truth. The source taxonomy should stay fixed to `internal`, `dice`, `rule`, and `fallback`, while `dice_backend`, `fallback_reason`, and `policy_profile` remain companion dimensions.

### C. Keep high-risk tuning opt-in, bounded, and seeded

The existing high-risk profile path should remain configuration-driven and guarded by:

- the shared KPI contract from Phase 9
- Phase 8 release semantics
- seeded comparisons that prove the effect is repeatable
- the locked activation threshold of `high_risk_profile_applied_rate >= 0.05`

This preserves the core idea of "prefer short-term phase-1 progress when configured" without turning it into a blanket override. It also gives execution a clear rule for when an apparent high-risk gain should still be reported as diagnostic-only.

### D. Explain KPI movement through source and policy deltas

Phase 10 diagnostics should answer:

- which candidate source mix changed relative to the control variant
- which policy or profile setting changed
- whether gate pass, fairness, denied high-risk lift, or reachability helped, harmed, mixed, or produced no material change
- whether the attribution confidence is `strong` or `tentative`

That explanation belongs beside the KPI outputs, not inside the primary acceptance decision itself.

## Artifact Contract Recommended For Phase 10

| Artifact | Producer | Why it matters |
|----------|----------|----------------|
| `candidate_quality_summary.json` | `run_phase_experiment_suite.py` | Canonical seeded summary of diversity, entropy, source-mix rates, and population metadata |
| `candidate_source_breakdown.csv` | suite and challenger workflows | Companion provenance breakdown across the locked source catalog plus companion dimensions |
| `generator_policy_impact_summary.json` | suite and challenger workflows | Comparative, control-baselined impact summary with metric labels and confidence |
| `phase_scale_seed_summary.csv` | `run_phase_experiment_suite.py` | Seed-level evidence with candidate-quality and high-risk tuning columns added beside KPI fields |
| `phase_scale_aggregate.json` | `run_phase_experiment_suite.py` | Aggregate repeated-seed evidence including candidate-quality rollups and high-risk summary means |
| `milestone_acceptance_summary.json` | `run_phase_experiment_suite.py` | Keeps milestone acceptance lightweight while linking to candidate-quality companions |
| `milestone_acceptance_review.md` | `run_phase_experiment_suite.py` | Derived narrative focused on decision explanation rather than dashboarding |

## Implementation Strategy By Plan Slice

### Slice 10-01: Instrument candidate diversity and generator provenance metrics

Focus:

- promote the locked diversity, entropy, and best-source metrics into seeded artifacts
- standardize the source catalog to `internal`, `dice`, `rule`, and `fallback`
- keep `denied` canonical and `high_risk_denied` companion
- make milestone evidence point to candidate-quality artifacts without making them gates

Primary files:

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`

### Slice 10-02: Harden short-term phase-1 fast-track tuning for high-risk paths

Focus:

- keep high-risk tuning bounded and explicit
- measure activation rate and seeded effect size under the `0.05` meaningful-activation floor
- distinguish strong evidence from anecdotal or diagnostic-only outcomes
- prove high-risk gains do not silently bypass fairness or reliability expectations

Primary files:

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`

### Slice 10-03: Publish generator and policy impact diagnostics beside batch KPIs

Focus:

- summarize which source or policy changes helped or harmed KPI outcomes against the control baseline
- keep machine-readable diagnostics canonical and comparative rather than causal
- derive concise review text from canonical diagnostics rather than bespoke markdown
- ensure the review surface stays explanation-first instead of becoming a dashboard

Primary files:

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
