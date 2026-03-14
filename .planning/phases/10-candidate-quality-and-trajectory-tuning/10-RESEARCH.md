# Phase 10: Candidate Quality and Trajectory Tuning - Research

**Researched:** 2026-03-15
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so existing batch-level candidate diversity, source entropy, and denied high-risk trajectory signals become seeded milestone evidence that explains which generator or policy shifts helped or harmed KPI outcomes?

## Planning Assumption

Phase 10 planning started before `10-CONTEXT.md` existed, so this research pass uses the roadmap, requirements, current state, and already-implemented runner code as the authoritative inputs. The key sources for this pass were:

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- Phase 8 and Phase 9 outputs
- current CLI and test code under `credit-coach/src/credit_coach/` and `credit-coach/tests/`

That is sufficient because `CAND-01`, `CAND-02`, and `CAND-03` are already concrete and the repo already contains most of the raw instrumentation needed for this phase.

## Executive Summary

Phase 10 should not invent a new candidate-generation stack. The repo already computes candidate diversity, candidate source entropy, denied high-risk lift, and high-risk reachability inside batch evaluation. What is missing is the layer that promotes those local metrics into seeded suite evidence, challenger comparisons, and milestone-ready diagnostics.

That makes this a promotion and explanation phase, not an algorithm-discovery phase. The main job is to make existing batch metrics durable across seeded runs, tie them to generator and policy provenance, and explain KPI movement in a way that is useful for milestone review. If execution tries to add too many new heuristics at once, it will blur the measurement contract that Phase 8 and Phase 9 just stabilized.

The recommended breakdown is:

- instrument candidate diversity and provenance in canonical seeded evidence
- harden the existing high-risk phase-1 tuning path with explicit bounds and seeded diagnostics
- publish generator and policy impact summaries beside batch KPI artifacts

## Existing Assets We Can Reuse

### Batch evaluation already computes candidate diversity and source entropy

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already computes candidate diversity from generated plan sets
  - already computes candidate source entropy across internal and DiCE-style generation paths
  - already writes batch summary payloads that can be promoted into seeded artifacts
- `credit-coach/tests/test_batch_candidate_diversity.py`
  - already locks the current diversity helpers and source-entropy behavior

This means `CAND-01` is mostly an aggregation and artifact-design problem.

### High-risk fast-track behavior already exists

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already exposes `_apply_high_risk_profile(...)`
  - already measures `denied_high_risk_lift`
  - already measures `high_risk_reachability_rate`
- `credit-coach/tests/test_batch_candidate_diversity.py`
  - already covers high-risk profile activation and guard conditions

This means `CAND-02` should harden and surface an existing path instead of introducing a second tuning system.

### Suite, challenger, and acceptance layers are now stable enough to extend

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already emits seeded summary CSVs
  - already emits aggregate JSON
  - already writes `kpi_contract_snapshot.json`
  - already writes `milestone_acceptance_summary.json`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already ranks variants using seeded KPI evidence
  - already carries denied high-risk lift and reachability metrics in challenger summaries

Phase 10 can therefore reuse the Phase 9 evidence contract instead of building a parallel reporting lane.

## External Patterns Worth Preserving

### Diverse recourse should stay measurable, not merely anecdotal

The DiCE line of work treats candidate diversity as a first-class property rather than a side effect of search. That supports promoting diversity and source-mix metrics into seeded evidence instead of burying them inside one-off batch summaries.

### Actionability beats aggressive search

Actionable recourse literature consistently favors constrained and feasible actions over superficially strong but unstable recommendations. That supports a Phase 10 design where high-risk fast-track tuning stays bounded by existing fairness and reliability gates rather than becoming an unconditional optimization path.

### Coaching-style systems need explanation, not only scores

Coaching-oriented credit interventions are most useful when they explain which strategy changed the near-term path. That supports generator and policy impact diagnostics as derived artifacts beside KPI snapshots, rather than only as raw numeric deltas.

## Gaps Phase 10 Must Close

### 1. Candidate-quality metrics stop at the batch boundary

Today the repo can measure diversity and source entropy inside batch evaluation, but seeded suite and milestone evidence do not surface those numbers as stable run-to-run signals. As a result, candidate quality exists locally but not at the milestone decision layer.

### 2. High-risk tuning is visible in code but not fully decision-ready

The repo already has opt-in high-risk profile logic and metrics, but seeded evidence does not yet explain:

- how often the profile activated
- whether it improved short-term phase-1 progress consistently
- whether the tuned path stayed inside reliability and fairness guardrails

### 3. Generator and policy impact is still hard to explain

Current outputs can show that KPI values moved, but not yet which source or policy shift most likely caused the move. That keeps `CAND-03` open even though many of the raw ingredients are already present.

### 4. Phase 10 must avoid swallowing Phase 11

It would be easy to turn this phase into a broader release-pack redesign, but telemetry-required production gates and outcome-feedback publication belong to Phase 11. Phase 10 should stay focused on candidate quality, trajectory tuning, and diagnostic explainability inside the existing seeded evidence contract.

## Recommended Architecture

### A. Extend seeded suite artifacts instead of inventing a second evidence lane

Promote batch-level candidate metrics into:

- `phase_scale_seed_summary.csv`
- `phase_scale_aggregate.json`
- `kpi_contract_snapshot.json` supporting-artifact references
- `milestone_acceptance_summary.json` supporting-artifact references

This keeps milestone evidence canonical while avoiding bloated acceptance payloads.

### B. Treat candidate provenance as machine-readable first

Phase 10 should write canonical companion artifacts such as:

- `candidate_quality_summary.json`
- `candidate_source_breakdown.csv`
- `generator_policy_impact_summary.json`

Human-readable review text can then derive from these artifacts without becoming the source of truth.

### C. Keep high-risk tuning opt-in, bounded, and seeded

The existing high-risk profile path should remain configuration-driven and guarded by:

- the shared KPI contract from Phase 9
- Phase 8 release semantics
- seeded comparisons that prove the effect is repeatable

This preserves the core idea of "prefer short-term phase-1 progress when configured" without turning it into a blanket override.

### D. Explain KPI movement through source and policy deltas

Phase 10 diagnostics should answer:

- which candidate source mix changed
- which policy or profile setting changed
- whether gate pass, fairness, denied high-risk lift, or reachability improved or worsened

That explanation belongs beside the KPI outputs, not inside the primary acceptance decision itself.

## Artifact Contract Recommended For Phase 10

| Artifact | Producer | Why it matters |
|----------|----------|----------------|
| `candidate_quality_summary.json` | `run_phase_experiment_suite.py` | Canonical seeded summary of diversity, entropy, and high-risk trajectory metrics |
| `candidate_source_breakdown.csv` | suite and challenger workflows | Source-mix and provenance breakdown across internal, DiCE, policy, and rule paths |
| `generator_policy_impact_summary.json` | suite and challenger workflows | Machine-readable explanation of which source or policy changes moved KPI outcomes |
| `phase_scale_seed_summary.csv` | `run_phase_experiment_suite.py` | Seed-level evidence with candidate-quality columns added beside KPI fields |
| `phase_scale_aggregate.json` | `run_phase_experiment_suite.py` | Aggregate repeated-seed evidence including candidate-quality rollups |
| `milestone_acceptance_summary.json` | `run_phase_experiment_suite.py` | Keeps milestone acceptance lightweight while linking to candidate-quality companions |
| `milestone_acceptance_review.md` | `run_phase_experiment_suite.py` | Derived narrative for human review using the machine-readable artifacts above |

## Implementation Strategy By Plan Slice

### Slice 10-01: Instrument candidate diversity and generator provenance metrics

Focus:

- promote existing diversity and source-entropy metrics into seeded artifacts
- standardize source labels and provenance rollups across suite and challenger
- make milestone evidence point to candidate-quality artifacts

Primary files:

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`

### Slice 10-02: Harden short-term phase-1 fast-track tuning for high-risk paths

Focus:

- keep high-risk tuning bounded and explicit
- measure activation rate and seeded effect size
- prove high-risk gains do not silently bypass fairness or reliability expectations

Primary files:

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`

### Slice 10-03: Publish generator and policy impact diagnostics beside batch KPIs

Focus:

- summarize which source or policy changes helped or harmed KPI outcomes
- keep machine-readable diagnostics canonical
- derive concise review text from canonical diagnostics rather than bespoke markdown

Primary files:

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
