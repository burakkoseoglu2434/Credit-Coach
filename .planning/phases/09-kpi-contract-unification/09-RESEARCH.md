# Phase 9: KPI Contract Unification - Research

**Researched:** 2026-03-14
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so smoke, phase-suite, and challenger workflows all enforce the same KPI meanings, reuse the same frozen model snapshot across seeded comparisons, and produce milestone acceptance from repeated evidence instead of a single green run?

## Planning Assumption

No `09-CONTEXT.md` exists because Phase 9 was planned directly from the roadmap. For this phase, the authoritative inputs are:

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- Phase 8 outputs and verification
- current runner code under `credit-coach/src/credit_coach/cli/`

That is sufficient because the phase scope is already tightly defined by `KPI-01`, `KPI-02`, and `KPI-03`.

## Executive Summary

Phase 8 gave the repo a shared release decision layer, but the KPI contract underneath it is still split across runners. `run_production_smoke.py` resolves thresholds and builds gate rows one way, `run_phase_experiment_suite.py` evaluates seed snapshots another way, and `run_model_challenger_matrix.py` still computes violation scores from its own mean-metric view. The repo therefore has a shared release decision output without a fully shared KPI evidence input.

The second missing piece is provenance. Phase-suite and challenger workflows create train run ids, but downstream batch and recourse execution still load the latest model bundle implicitly. That means repeated seeded comparisons are only mostly frozen, not explicitly frozen. For `KPI-02`, the contract must move from "train once, hope latest stays stable" to "pin an explicit model bundle and carry that reference through every seed."

The third missing piece is milestone acceptance. The repo already writes seed summaries, aggregate release metrics, and smoke artifacts, but there is not yet one canonical acceptance artifact that says the milestone passed because repeated seeded evidence passed under a fixed model snapshot. Phase 9 should therefore be planned as:

- shared KPI semantics
- explicit frozen-model provenance
- repeated-evidence acceptance artifacts

not as a new modeling phase.

## Existing Assets We Can Reuse

### Threshold loading and release semantics already exist

- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - loads default and file-based thresholds
  - already knows the canonical threshold key names
- `credit-coach/src/credit_coach/ops/release_decision.py`
  - already separates lift, reliability, and fairness precedence
  - already emits `GO | LIMITED_GO | NO_GO`

Phase 9 should build on these modules instead of inventing another gate layer inside a CLI.

### Phase-suite already emits repeated-seed evidence

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - writes `phase_scale_seed_summary.csv`
  - writes `phase_scale_aggregate.json`
  - writes `release_decision.json`
  - captures `train_run_id` for the train-once path

This is the natural place to anchor milestone acceptance, because it already owns repeated-seed evidence.

### Smoke already has the strongest operator-facing artifact shape

- `credit-coach/src/credit_coach/cli/run_production_smoke.py`
  - resolves thresholds
  - writes `kpi_snapshot.json`
  - writes `production_smoke_report.json`
  - can already consume `phase_scale_aggregate.json`

Smoke therefore gives Phase 9 a good template for runner outputs, but its helper logic must be shared rather than staying smoke-only.

### Model bundle storage already has enough structure

- `credit-coach/src/credit_coach/model/registry.py`
  - saves versioned model bundles
  - writes `artifacts/models/<model_version>/manifest.json`
  - maintains `latest.json`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already writes `batch_run_manifest.json`
  - already records `model_version` in `batch_summary.json`

The repo is close to explicit freezing already. The real gap is that loaders still default to `latest.json` instead of an explicit requested bundle.

## Gaps Phase 9 Must Close

### 1. KPI semantics still drift across runners

Today the same threshold contract is interpreted in three slightly different ways:

- suite computes seed contract snapshots
- smoke builds gate rows plus a KPI snapshot
- challenger computes violation score from mean metrics

This creates room for subtle disagreement in:

- metric names
- min versus max comparator direction
- failed-check strings
- what counts as release-blocking versus informational

Phase 9 needs one shared comparator and snapshot layer beneath all three runners.

### 2. Frozen model state is implicit, not explicit

`run_phase_experiment_suite.py` can train once before seeded batches, but downstream runs still load the latest model bundle through `load_latest_model_bundle(...)`. `run_model_challenger_matrix.py` also retrains repeatedly and then relies on later steps to pick up the right bundle. This is workable in a quiet repo, but it is not a strong freeze contract.

Phase 9 must make the chosen bundle explicit through model version or manifest references carried into every seeded run.

### 3. Milestone acceptance is still too runner-local

The repo can already tell whether:

- one smoke run passed
- one suite aggregate passed
- one challenger variant looks best

What it cannot yet say cleanly is:

"this milestone is acceptable because repeated seeded evidence under a fixed model snapshot satisfied the shared KPI contract."

That is the core of `KPI-03`.

### 4. Human review text is ahead of canonical acceptance data

`release_review_summary.md` already exists, which is helpful. But Phase 9 needs acceptance review to be derived from a canonical machine-readable acceptance artifact, not treated as the primary source of truth.

## Recommended Architecture

### A. Promote `ops/kpi_contract.py` into the canonical KPI semantics layer

Keep `load_kpi_thresholds(...)`, but add shared helpers for:

- resolved threshold extraction
- normalized KPI metric payloads
- min/max comparator evaluation
- failed-check collection
- KPI snapshot generation
- violation scoring inputs for challenger ranking

This keeps threshold names, comparator direction, and snapshot fields centralized.

### B. Add explicit frozen-model resolution to the model registry contract

Extend registry and runner wiring so workflows can request:

- a specific `model_version`
- or a specific manifest path

instead of always loading `latest.json`.

This should feed:

- `run_batch_recourse_eval.py`
- `run_recourse.py`
- `run_phase_experiment_suite.py`
- `run_model_challenger_matrix.py`

### C. Treat repeated-seed suite output as the milestone acceptance anchor

Do not move acceptance to smoke. Smoke is still a release gate, but milestone acceptance for this phase should come from repeated seeded evidence plus frozen-model provenance. The suite should therefore write a canonical acceptance artifact and smoke should consume it when available.

### D. Keep human-readable review derived from machine-readable evidence

Continue generating markdown summaries, but make them derived companions to JSON and CSV artifacts. That prevents narrative drift and keeps automation reliable.

## Artifact Contract Recommended For Phase 9

| Artifact | Producer | Why it matters |
|----------|----------|----------------|
| `phase_scale_seed_summary.csv` | `run_phase_experiment_suite.py` | Seed-level repeated evidence with explicit model provenance columns |
| `phase_scale_aggregate.json` | `run_phase_experiment_suite.py` | Aggregate repeated-seed KPI evidence consumed by smoke and acceptance logic |
| `frozen_model_manifest.json` | suite and challenger workflows | Canonical pointer to the trained bundle reused across seeded comparisons |
| `batch_run_manifest.json` | `run_batch_recourse_eval.py` | Per-seed provenance showing which model snapshot actually ran |
| `release_decision.json` | suite and smoke | Shared release classification layered on top of aligned KPI evidence |
| `milestone_acceptance_summary.json` | suite | Canonical machine-readable decision for `KPI-03` |
| `milestone_acceptance_review.md` | suite | Human-readable derived summary for release and milestone review |

## Implementation Strategy By Plan Slice

### Slice 09-01: Shared KPI semantics across runners

Focus:

- eliminate runner-specific KPI comparator drift
- reuse shared threshold semantics in suite, smoke, and challenger
- align failed-check naming and snapshot payloads

Primary files:

- `credit-coach/src/credit_coach/ops/kpi_contract.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_production_smoke.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`

### Slice 09-02: Explicit frozen-model seeded execution

Focus:

- make model bundle selection explicit
- stop relying on `latest.json` for seeded comparison correctness
- preserve variant-scoped training provenance in challenger runs

Primary files:

- `credit-coach/src/credit_coach/model/registry.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`

### Slice 09-03: Repeated-evidence milestone acceptance

Focus:

- derive milestone acceptance from seeded evidence
- let smoke prefer seeded evidence when available
- stop single winning runs from silently dominating milestone decisions

Primary files:

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
- `credit-coach/src/credit_coach/cli/run_production_smoke.py`

## Key Risks And How To Plan Around Them

### Risk: threshold drift survives inside convenience helpers

Planning implication:

- remove or shrink runner-private KPI evaluators
- keep one canonical comparator path

### Risk: "train once" still allows hidden snapshot changes

Planning implication:

- pass explicit model references into downstream CLIs
- fail closed when the requested snapshot cannot be resolved

### Risk: acceptance artifacts duplicate Phase 11 release packaging

Planning implication:

- keep Phase 9 acceptance artifacts lightweight and decision-focused
- leave full release packet standardization to Phase 11

### Risk: single-run smoke accidentally overrides repeated evidence

Planning implication:

- make smoke prefer seeded aggregate inputs when available
- clearly label single-seed fallback as degraded evidence

## Validation Architecture

### Existing tests are enough for Phase 9

The repo already has strong coverage at the runner seam level:

- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach/tests/test_production_smoke.py`
- `credit-coach/tests/test_challenger_matrix_selection.py`
- `credit-coach/tests/test_release_decision.py`

Phase 9 should extend these tests instead of creating a parallel verification stack.

### Verification approach

- use runner-level contract tests to prove semantic alignment
- use suite and challenger tests to prove frozen-model reuse
- use suite plus smoke tests to prove milestone acceptance prefers repeated seeded evidence

## Recommendation

Plan Phase 9 as three execution slices that build on one another:

1. align KPI semantics
2. freeze model provenance
3. derive milestone acceptance from repeated seeded evidence

That order keeps the phase incremental and avoids hardening acceptance logic on top of drifting inputs.
