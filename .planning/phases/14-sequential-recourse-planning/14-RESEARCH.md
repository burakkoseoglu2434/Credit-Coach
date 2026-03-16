# Phase 14: Sequential Recourse Planning - Research

**Researched:** 2026-03-16
**Status:** Ready for replanning
**Confidence:** HIGH

## Planning Question

What has to change so Credit Coach can move from behavior-aware one-shot recommendations toward canonical multi-phase trajectories with dynamic, time-aware risk simulation?

## Planning Basis

Phase 14 now has a locked `14-CONTEXT.md`. For this replanning pass, the authoritative sources are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/research/v1.2-RECOMMENDATION-QUALITY-HARDENING.md`
- `.planning/phases/12-action-realism-feasibility-expansion/12-CONTEXT.md`
- `.planning/phases/12-action-realism-feasibility-expansion/12-RESEARCH.md`
- `.planning/phases/13-behavior-aware-recourse/13-CONTEXT.md`
- `.planning/phases/13-behavior-aware-recourse/13-RESEARCH.md`
- `.planning/phases/14-sequential-recourse-planning/14-CONTEXT.md`
- current recommendation code under `credit-coach/src/credit_coach/`
- current tests under `credit-coach/tests/`

That is sufficient because the milestone goal, the brownfield codebase seam, and the remaining Phase 14 gray areas are now all locked. This pass therefore replans Phase 14 from milestone intent, brownfield code reality, and explicit trajectory decisions rather than from open-ended discovery.

## Executive Summary

Phase 14 should not invent a brand-new planner stack. The repo already contains much of the raw material for sequential planning:

- typed actions already carry `time_months`, `phase_id`, and week windows
- the generator already groups actions into early, middle, and later timing buckets
- `run_recourse.py` already emits a roadmap-style phased view and checkpoint estimates
- batch evaluation already computes 4w, 12w, and 24w trajectory metrics
- the weekly coaching loop already simulates execution over time
- Phase 13 now adds execution likelihood and partial-execution robustness evidence

The gap is that these pieces are still mostly descriptive or post-hoc. The core planner still chooses a flattened plan, then reporting layers derive phased views afterward. Phase 14 should make phased trajectory structure first-class, upgrade trajectory simulation into a dynamic planning seam rather than a reporting-only rollup, and make ranking balance short-term feasibility against longer-horizon risk improvement without weakening inherited fairness, reliability, telemetry, and acceptance contracts.

The safest brownfield strategy is:

- formalize one canonical multi-phase trajectory contract in schemas and serialization, with `phases[]` as the semantic source of truth and `actions[]` preserved for compatibility
- make generator and planner produce phase-aware trajectories instead of only a flattened action list
- reuse the weekly coaching loop as the dynamic simulation grain, but make it trajectory-aware and review-driven at phase boundaries
- keep inherited gate logic authoritative and let phase-aware optimization reorder only eligible plans with short-term health prioritized over long-horizon upside
- publish stable trajectory evidence that batch, suite, challenger, and release review can aggregate without redefining the KPI contract

The locked context sharpens that strategy further:

- canonical trajectory semantics live in `phases[]`, not in a reporting-only projection
- the phase vocabulary stays fixed:
  - `phase_1_stabilize`
  - `phase_2_build`
  - `phase_3_optimize`
- one action belongs to one primary phase; repeated interventions become new steps
- the primary checkpoint is `4 hafta`, with checkpoint priority ordered as `4w > 12w > 24w`
- checkpoint regression is handled as soft penalty rather than strict invalidation
- the trajectory model is hybrid: fixed phases plus review-based adaptive transitions
- optimizer policy stays short-term-first and becomes more conservative for high-risk trajectories
- optimizer outputs should remain interpretable through labels such as `stabilize_first`, `balanced_progress`, and `long_horizon_heavy`

## Existing Assets We Can Reuse

### Phase metadata already exists in core recommendation objects

- `credit-coach/src/credit_coach/data/schema.py`
  - `PlanAction` already carries:
    - `time_months`
    - `phase_id`
    - `week_start`
    - `week_end`
  - `PlanRecord` already carries behavior-aware and trajectory-adjacent fields
- `credit-coach/src/credit_coach/recourse/generator.py`
  - already maps months into:
    - `phase_1_stabilize`
    - `phase_2_build`
    - `phase_3_optimize`
  - already builds weekly action plans when the weekly optimizer is enabled

This means Phase 14 does not need to invent phase semantics from scratch. It can promote the existing timing vocabulary into a canonical planning contract.

### Roadmap and checkpoint reporting already exist

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - already emits phased roadmap structures, step rows, and checkpoint estimates for week 4, week 12, and week 24
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already computes:
    - `trajectory_pd_4w`
    - `trajectory_pd_12w`
    - `trajectory_pd_24w`
    - `trajectory_gate_pass_*`
    - `trajectory_partial_progress`
    - phase action counts

Phase 14 should treat these as a brownfield asset, not parallel them with a second incompatible reporting layer.

### Weekly execution simulation is already the correct dynamic seam

- `credit-coach/src/credit_coach/coaching/loop.py`
  - already supports weekly execution, dropout, replan triggers, and execution-rate summaries
- Phase 13 already locked this weekly loop as the canonical execution seam

That makes it the right foundation for dynamic trajectory simulation in Phase 14.

### Planner and governance seams are already explicit

- `credit-coach/src/credit_coach/coaching/planner.py`
  - already does gate-first ordering and now uses expected PD improvement under Phase 13
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already carries trajectory guardrails and milestone-review rendering
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already aggregates seeded trajectory and behavior-aware evidence
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already compares trajectory and behavior-aware metrics across variants

Phase 14 can therefore strengthen trajectory planning without reopening the governance contract.

## Gaps Phase 14 Must Close

### 1. Trajectory structure is still mostly derived, not canonical

The repo already knows action timing, but the canonical planning object is still effectively a flat plan with action rows. Phase 14 must elevate trajectory phases into first-class, machine-readable plan structure.

### 2. Trajectory simulation is not yet a planning primitive

Current trajectory metrics are useful, but they are largely computed after a recommendation is chosen. Phase 14 must let dynamic trajectory behavior influence planning rather than remaining a downstream report.

### 3. Optimization is still one-shot biased

Phase 13 added expected utility, but the main ranking still prioritizes nominal one-plan outcomes. Phase 14 must explicitly balance:

- short-term feasibility
- near-term gate progress
- medium-term improvement
- longer-horizon risk reduction

without allowing long-term optimism to hide short-term infeasibility.

## Recommended Architecture

### A. Promote phased trajectory structure into canonical schemas

The cleanest direction is to keep `PlanRecord` as the top-level object, but add explicit trajectory-phase structure instead of relying only on flattened action rows plus derived roadmap JSON. The locked context now makes this more specific:

- keep both `actions[]` and `phases[]`
- treat `phases[]` as canonical trajectory semantics
- keep the phase set fixed and explicit
- require phase-level metadata such as `target_pd`, `gate_pass_target`, and `review_week`

Likely touchpoints:

- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/recourse/generator.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`

### B. Generate trajectories, not only sorted actions

The generator should still be allowed to build action candidates the current way, but Phase 14 should introduce a canonical grouping and sequencing layer so near-, mid-, and long-horizon actions are planned as one trajectory object rather than only as a flat list sorted by month. The context also rules out one ambiguity: a single action should not span multiple phases. If repeated intervention is needed, it should become a new step.

### C. Reuse the weekly loop as the dynamic trajectory simulator

The right simulation strategy is to keep the weekly coaching loop as the execution grain, then layer time-aware trajectory checkpoints and risk inertia on top of it. Review-driven adaptive transitions should happen at phase boundaries:

- week 4
- week 12
- optional week 24 closeout

That avoids simulator drift, keeps Phase 14 consistent with Phase 13 behavior-aware evidence, and matches the locked hybrid replan model.

### D. Keep optimization gate-first and phase-aware second

The phase-aware objective should only operate after inherited constraint, fairness, reliability, telemetry, and release eligibility semantics. It should not create a second path that can promote unsafe trajectories because their long-run outcome looks good. The locked policy now makes this explicit:

- early checkpoint health is primary
- medium-horizon confirmation is secondary
- long-horizon upside is tertiary
- high-risk segments get a more conservative version of the same weighting

### E. Keep evidence machine-readable and seeded

Phase 14 should continue the artifact pattern established in earlier phases:

- canonical machine-readable summary
- seeded suite aggregation
- challenger-compatible variant comparison
- explanation-first markdown derived from those artifacts

Trajectory evidence should therefore live in stable JSON or CSV artifacts rather than only in the release-review markdown.
Trajectory artifacts should also carry transition state so later phases can reason about `on_track`, `needs_replan`, and `degraded` trajectories without inventing a new tracking layer.

## Recommended Plan Breakdown

### Plan 14-01: Multi-phase planning model

Focus on formalizing canonical trajectory phases and phase-aware serialization for near-, mid-, and longer-horizon actions.

### Plan 14-02: Dynamic trajectory simulation

Focus on time-aware PD evolution, partial execution, inertia, and checkpoint behavior using the existing weekly execution seam.

### Plan 14-03: Phase-aware optimization objective

Focus on ranking trajectories by balancing short-term feasibility with longer-horizon risk improvement under inherited gates.

## Risks To Watch

- building a second trajectory representation that drifts from the current roadmap and checkpoint outputs
- using long-horizon gains to hide poor short-term feasibility or gate progress
- splitting simulation across two incompatible time models instead of extending the weekly loop
- publishing trajectory intelligence only in markdown rather than in stable machine-readable artifacts

## Recommendation

Proceed with Phase 14 now. The repository is ready: Phase 12 made actions explicit, Phase 13 made follow-through explicit, and the gray areas that most affect outcome are now locked. The replan should therefore focus on implementing one canonical `phases[]` contract, review-driven transitions, and short-term-first phase-aware optimization rather than reopening scope.
